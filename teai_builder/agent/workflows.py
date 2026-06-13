"""Built-in workflow templates for common development pipelines."""

from __future__ import annotations

from teai_builder.agent.workflow_engine import WorkflowDefinition, WorkflowStep, register_workflow


def _register_builtins() -> None:
    register_workflow(
        WorkflowDefinition(
            workflow_id="app_build_v1",
            name="App Build Pipeline",
            description="Research, plan, scaffold, and preview an application.",
            input_schema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "platform": {"type": "string", "enum": ["web", "mobile", "desktop"]},
                },
                "required": ["project_name", "platform"],
            },
            steps=[
                WorkflowStep(
                    step_id="research",
                    name="Research latest stack and project requirements.",
                    prompt_template=(
                        "Goal: build '{project_name}' for '{platform}'.\n"
                        "Research the latest recommended libraries, SDKs, and project structure for this platform. "
                        "Return a concise report covering: framework, language, dependencies, platform notes, and any gotchas."
                    ),
                ),
                WorkflowStep(
                    step_id="plan",
                    name="Create implementation plan.",
                    prompt_template=(
                        "Based on the research, create a step-by-step implementation plan for '{project_name}' on '{platform}'. "
                        "Break it into phases, tasks, and acceptance criteria."
                    ),
                    depends_on=["research"],
                ),
                WorkflowStep(
                    step_id="scaffold",
                    name="Scaffold project files.",
                    prompt_template=(
                        "Create the project scaffold for '{project_name}' on '{platform}' following the plan. "
                        "Initialize the project, configure dependencies, and prepare a preview entrypoint."
                    ),
                    depends_on=["plan"],
                    checkpoint_after=True,
                ),
                WorkflowStep(
                    step_id="verify",
                    name="Verify build and preview.",
                    prompt_template=(
                        "Verify the '{project_name}' scaffold builds cleanly and the preview renders. "
                        "Fix any issues found."
                    ),
                    depends_on=["scaffold"],
                    checkpoint_after=True,
                ),
            ],
        )
    )


_register_builtins()
