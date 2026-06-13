"""Parallel execution engine for subagent task orchestration."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Awaitable, Callable

from loguru import logger

from teai_builder.agent.goal_validator import Goal, ValidationResult, get_goal_validator
from teai_builder.agent.subagent import SubagentManager
from teai_builder.bus.events import OutboundMessage
from teai_builder.bus.queue import MessageBus
from teai_builder.security.workspace_access import WorkspaceScope


class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    BLOCKED = auto()
    CANCELLED = auto()


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: float = 0.0
    finished_at: float = 0.0
    upstream_ids: list[str] = field(default_factory=list)
    downstream_ids: list[str] = field(default_factory=list)


@dataclass
class ParallelTask:
    goal_id: str
    task_id: str
    description: str
    prompt: str
    model: str | None = None
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)


class ParallelExecutor:
    def __init__(
        self,
        subagent_manager: SubagentManager,
        bus: MessageBus,
        max_parallel: int = 3,
    ) -> None:
        self.subagent_manager = subagent_manager
        self.bus = bus
        self.max_parallel = max_parallel
        self.goal_validator = get_goal_validator()
        self._results: dict[str, TaskResult] = {}

    def _model_for(self, task: ParallelTask) -> str:
        return task.model or self.subagent_manager.model

    async def execute(self, goal: Goal, tasks: list[ParallelTask]) -> dict[str, TaskResult]:
        results: dict[str, TaskResult] = {}
        pending = {t.task_id: t for t in tasks}
        completed: set[str] = set()

        while pending:
            ready = [
                t for t in pending.values()
                if t.status == TaskStatus.PENDING
                and all(dep in completed for dep in t.depends_on)
            ]
            if not ready:
                blocked = [t.task_id for t in pending.values() if t.status == TaskStatus.PENDING]
                if blocked:
                    raise RuntimeError(f"Deadlocked tasks with unmet dependencies: {blocked}")
                break

            running: list[Awaitable[TaskResult]] = []
            selected = ready[: self.max_parallel]
            for task in selected:
                task.status = TaskStatus.RUNNING
                running.append(self._run_task(goal, task))

            batch = await asyncio.gather(*running, return_exceptions=True)
            for task, raw in zip(selected, batch):
                if isinstance(raw, Exception):
                    task.status = TaskStatus.FAILED
                    results[task.task_id] = TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.FAILED,
                        error=str(raw),
                    )
                else:
                    results[task.task_id] = raw
                    task.status = raw.status
                pending.pop(task.task_id, None)
                if results[task.task_id].status == TaskStatus.COMPLETED:
                    completed.add(task.task_id)

        self._results.update(results)
        return results

    async def _run_task(self, goal: Goal, task: ParallelTask) -> TaskResult:
        started_at = asyncio.get_event_loop().time()
        status = TaskStatus.RUNNING
        output: dict[str, Any] = {}
        error: str | None = None
        try:
            result = await self.subagent_manager.spawn(
                label=f"{goal.goal_id}:{task.task_id}",
                task_description=task.description,
                prompt=task.prompt,
                model=self._model_for(task),
            )
            output = result or {}
            if result and result.get("status") == "error":
                status = TaskStatus.FAILED
                error = str(result.get("error"))
            else:
                status = TaskStatus.COMPLETED
        except Exception as exc:
            status = TaskStatus.FAILED
            error = str(exc)
        finished_at = asyncio.get_event_loop().time()
        return TaskResult(
            task_id=task.task_id,
            status=status,
            output=output,
            error=error,
            started_at=started_at,
            finished_at=finished_at,
        )
