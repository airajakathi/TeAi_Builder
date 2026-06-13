"""Deterministic workflow engine for reproducible agent pipelines."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from teai_builder.agent.parallel_executor import ParallelExecutor, ParallelTask, TaskResult
from teai_builder.agent.checkpoint import Checkpoint, get_checkpoint_store
from teai_builder.agent.goal_validator import Goal, get_goal_validator


class WorkflowState:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    prompt_template: str
    depends_on: list[str] = field(default_factory=list)
    max_retries: int = 0
    checkpoint_after: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str
    steps: list[WorkflowStep]
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRun:
    run_id: str
    workflow_id: str
    goal_id: str
    state: str = WorkflowState.PENDING
    current_step: str | None = None
    step_results: dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    def __init__(
        self,
        parallel_executor: ParallelExecutor,
        storage_dir: Path | None = None,
    ) -> None:
        self.parallel_executor = parallel_executor
        self.checkpoint_store = get_checkpoint_store()
        self.goal_validator = get_goal_validator()
        if storage_dir is None:
            storage_dir = Path.home() / ".teai_builder" / "workflows"
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, run_id: str) -> Path:
        return self.storage_dir / f"{run_id}.json"

    def save_run(self, run: WorkflowRun) -> Path:
        path = self._path_for(run.run_id)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._run_to_dict(run), f, indent=2)
        tmp.replace(path)
        return path

    def load_run(self, run_id: str) -> WorkflowRun | None:
        path = self._path_for(run_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self._run_from_dict(data)

    def _run_to_dict(self, run: WorkflowRun) -> dict[str, Any]:
        return {
            "run_id": run.run_id,
            "workflow_id": run.workflow_id,
            "goal_id": run.goal_id,
            "state": run.state,
            "current_step": run.current_step,
            "step_results": run.step_results,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "error": run.error,
            "metadata": run.metadata,
        }

    def _run_from_dict(self, data: dict[str, Any]) -> WorkflowRun:
        return WorkflowRun(
            run_id=data["run_id"],
            workflow_id=data["workflow_id"],
            goal_id=data["goal_id"],
            state=data.get("state", WorkflowState.PENDING),
            current_step=data.get("current_step"),
            step_results=data.get("step_results", {}),
            started_at=data.get("started_at", time.time()),
            finished_at=data.get("finished_at"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )

    async def run(self, definition: WorkflowDefinition, goal: Goal, variables: dict[str, Any]) -> WorkflowRun:
        run = WorkflowRun(
            run_id=f"{definition.workflow_id}:{int(time.time())}",
            workflow_id=definition.workflow_id,
            goal_id=goal.goal_id,
            state=WorkflowState.RUNNING,
        )
        self.save_run(run)

        try:
            task_map = self._build_task_map(definition, goal, variables)
            results = await self.parallel_executor.execute(goal, list(task_map.values()))
            for step in definition.steps:
                task = task_map[step.step_id]
                result = results.get(step.step_id)
                if result and result.status == TaskStatus.COMPLETED:
                    run.step_results[step.step_id] = result.output
                else:
                    run.state = WorkflowState.FAILED
                    run.error = result.error if result else "Unknown task failure"
                    self.save_run(run)
                    return run
            run.state = WorkflowState.COMPLETED
        except Exception as exc:
            run.state = WorkflowState.FAILED
            run.error = str(exc)
            logger.exception("Workflow {} failed", run.run_id)
        finally:
            run.finished_at = time.time()
            self.save_run(run)
        return run

    def _build_task_map(
        self,
        definition: WorkflowDefinition,
        goal: Goal,
        variables: dict[str, Any],
    ) -> dict[str, ParallelTask]:
        task_map: dict[str, ParallelTask] = {}
        for step in definition.steps:
            prompt = step.prompt_template.format(**variables)
            task_map[step.step_id] = ParallelTask(
                goal_id=goal.goal_id,
                task_id=step.step_id,
                description=step.name,
                prompt=prompt,
                depends_on=step.depends_on,
                metadata={"workflow_step": True},
            )
        return task_map


# Preset workflow library shipped with the platform.
_BUILTIN_WORKFLOWS: dict[str, WorkflowDefinition] = {}


def register_workflow(definition: WorkflowDefinition) -> None:
    _BUILTIN_WORKFLOWS[definition.workflow_id] = definition


def get_workflow(workflow_id: str) -> WorkflowDefinition | None:
    return _BUILTIN_WORKFLOWS.get(workflow_id)


def load_workflows_from_dir(workflows_dir: Path) -> None:
    if not workflows_dir.exists():
        return
    for path in workflows_dir.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            definition = WorkflowDefinition(
                workflow_id=data["workflow_id"],
                name=data["name"],
                description=data.get("description", ""),
                steps=[
                    WorkflowStep(
                        step_id=step["step_id"],
                        name=step["name"],
                        prompt_template=step["prompt_template"],
                        depends_on=step.get("depends_on", []),
                        max_retries=step.get("max_retries", 0),
                        checkpoint_after=step.get("checkpoint_after", False),
                    )
                    for step in data.get("steps", [])
                ],
            )
            register_workflow(definition)
        except Exception as exc:
            logger.warning("Failed to load workflow from {}: {}", path, exc)
