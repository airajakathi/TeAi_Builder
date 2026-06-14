"""Deterministic workflow engine for reproducible agent pipelines."""

from __future__ import annotations

import asyncio
import dataclasses
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
            validation = self.goal_validator.validate(goal, run.step_results)
            if validation.is_complete is False:
                run.state = WorkflowState.FAILED
                run.error = (
                    "Goal validation failed: "
                    + ", ".join(validation.failed_criteria or ["unknown failure"])
                )
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


class DynamicWorkflowExecutor:
    """Adaptive workflow executor with retries, fallback steps, and self-healing."""

    def __init__(
        self,
        workflow_engine: WorkflowEngine,
        max_retries: int = 2,
        fallback_prompt: str | None = None,
    ) -> None:
        self.workflow_engine = workflow_engine
        self.max_retries = max_retries
        self.fallback_prompt = fallback_prompt or (
            "The previous attempt failed. Analyze the error, adjust the plan, "
            "and continue toward the goal."
        )

    async def execute(self, definition: WorkflowDefinition, goal: Goal, variables: dict[str, Any]) -> WorkflowRun:
        run = WorkflowRun(
            run_id=f"{definition.workflow_id}:{int(time.time())}",
            workflow_id=definition.workflow_id,
            goal_id=goal.goal_id,
            state=WorkflowState.RUNNING,
        )
        self.workflow_engine.save_run(run)

        try:
            task_map = self.workflow_engine._build_task_map(definition, goal, variables)
            results: dict[str, TaskResult] = {}

            for step in definition.steps:
                task = task_map[step.step_id]
                result = await self._run_step_with_retries(goal, task, step, results)
                results[step.step_id] = result
                if result.status == TaskStatus.COMPLETED:
                    run.step_results[step.step_id] = result.output
                else:
                    run.state = WorkflowState.FAILED
                    run.error = result.error or "Dynamic workflow step failed"
                    self.workflow_engine.save_run(run)
                    return run

            validation = self.workflow_engine.goal_validator.validate(goal, run.step_results)
            if validation.is_complete is False:
                run.state = WorkflowState.FAILED
                run.error = (
                    "Goal validation failed: "
                    + ", ".join(validation.failed_criteria or ["unknown failure"])
                )
                self.workflow_engine.save_run(run)
                return run

            run.state = WorkflowState.COMPLETED
        except Exception as exc:
            run.state = WorkflowState.FAILED
            run.error = str(exc)
            logger.exception("Dynamic workflow {} failed", run.run_id)
        finally:
            run.finished_at = time.time()
            self.workflow_engine.save_run(run)
        return run

    async def _run_step_with_retries(
        self,
        goal: Goal,
        task: ParallelTask,
        step: WorkflowStep,
        prior_results: dict[str, TaskResult],
    ) -> TaskResult:
        last_result: TaskResult | None = None
        for attempt in range(1, max(step.max_retries, 1) + 1):
            if attempt > 1:
                enriched_prompt = self._enrich_prompt_with_failure(task.prompt, last_result, prior_results)
                task = dataclasses.replace(task, prompt=enriched_prompt)
            last_result = await self.workflow_engine.parallel_executor._run_task(goal, task)
            if last_result.status == TaskStatus.COMPLETED:
                return last_result
            if step.max_retries and attempt < max(step.max_retries, 1):
                await asyncio.sleep(min(2 ** attempt, 10))

        return last_result or TaskResult(task_id=task.task_id, status=TaskStatus.FAILED, error="Unknown task failure")

    def _enrich_prompt_with_failure(self, prompt: str, last_result: TaskResult | None, prior_results: dict[str, TaskResult]) -> str:
        context_lines = [prompt, "", "Previous attempt failed."]
        if last_result and last_result.error:
            context_lines.append(f"Failure reason: {last_result.error}")
        if prior_results:
            context_lines.append("Prior step outputs:")
            for step_id, result in prior_results.items():
                output = result.output.get("output") if isinstance(result.output, dict) else result.output
                context_lines.append(f"- {step_id}: {output}")
        context_lines.append(self.fallback_prompt)
        return "\n".join(context_lines)


class ContextCompactor:
    """Compacts workflow context when context size grows too large."""

    def __init__(self, max_chars: int = 12000) -> None:
        self.max_chars = max_chars

    def compact(self, context: str) -> str:
        if len(context) <= self.max_chars:
            return context
        head = context[: self.max_chars // 2]
        tail = context[-self.max_chars // 2 :]
        return "\n".join([head, "...", "... context trimmed ...", "...", tail])


class SemanticCheckpointTrigger:
    """Suggests checkpoint creation based on workflow semantics."""

    def __init__(self, keywords: tuple[str, ...] | None = None) -> None:
        self.keywords = keywords or (
            "scaffold",
            "plan",
            "implement",
            "review",
            "validate",
        )

    def should_checkpoint(self, step: WorkflowStep) -> bool:
        text = f"{step.step_id} {step.name} {step.prompt_template}".lower()
        return any(keyword in text for keyword in self.keywords)
