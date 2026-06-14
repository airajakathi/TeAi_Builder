"""Project scaffolding tool for TeAI Builder."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from teai_builder.agent.tools.base import Tool, tool_parameters
from teai_builder.agent.tools.schema import (
    BooleanSchema,
    StringSchema,
    tool_parameters_schema,
)


@tool_parameters(
    tool_parameters_schema(
        project_name=StringSchema("Name of the project to scaffold"),
        platform=StringSchema(
            "Target platform",
            enum=["web", "mobile", "desktop"],
        ),
        template=StringSchema(
            "Optional template or starter name",
            nullable=True,
        ),
        force=BooleanSchema(
            description="Overwrite existing project files if present.",
            default=False,
            nullable=True,
        ),
        required=["project_name", "platform"],
    )
)
class ScaffoldProjectTool(Tool):
    """Scaffold a new project in the current workspace."""

    _scopes = {"core", "subagent"}

    def __init__(
        self,
        workspace: str | Path | None = None,
        restrict_to_workspace: bool = False,
    ) -> None:
        self._workspace = Path(workspace) if workspace is not None else None
        self._restrict_to_workspace = restrict_to_workspace

    @property
    def name(self) -> str:
        return "scaffold_project"

    @property
    def description(self) -> str:
        return (
            "Create a new project scaffold for the requested platform. "
            "Uses the latest known starter when possible."
        )

    def _resolve_project_dir(self, project_name: str) -> Path:
        base = (
            self._workspace
            if self._restrict_to_workspace and self._workspace is not None
            else Path.cwd()
        )
        return (base / project_name).resolve()

    async def execute(
        self,
        project_name: str,
        platform: str,
        template: str | None = None,
        force: bool = False,
        **kwargs: Any,
    ) -> Any:
        project_dir = self._resolve_project_dir(project_name)

        if project_dir.exists() and not force:
            return f"Error: project already exists at {project_dir}. Use force=true to overwrite."

        if project_dir.exists() and force:
            shutil.rmtree(project_dir)

        try:
            if platform == "mobile":
                return self._scaffold_mobile(project_dir, project_name, template)
            if platform == "web":
                return self._scaffold_web(project_dir, project_name, template)
            if platform == "desktop":
                return self._scaffold_desktop(project_dir, project_name, template)
            return f"Error: unsupported platform '{platform}'"
        except Exception as exc:
            return f"Error scaffolding project: {exc}"

    def _scaffold_mobile(self, project_dir: Path, project_name: str, template: str | None) -> str:
        cmd = [
            "npx",
            "--yes",
            "create-expo-app@latest",
            str(project_dir),
            "--template",
            "blank-typescript",
        ]
        if template:
            cmd[cmd.index("blank-typescript")] = template

        completed = subprocess.run(
            cmd,
            cwd=project_dir.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return (
                "Error: create-expo-app failed.\n\n"
                f"STDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}"
            )
        return (
            "Scaffolded Expo project.\n\n"
            f"- Path: {project_dir}\n"
            f"- Command: {' '.join(cmd)}\n\n"
            "Next: run `npx expo start` inside the project."
        )

    def _scaffold_web(self, project_dir: Path, project_name: str, template: str | None) -> str:
        cmd = [
            "npx",
            "--yes",
            "create-vite@latest",
            str(project_dir),
            "--template",
            "ts",
        ]
        completed = subprocess.run(
            cmd,
            cwd=project_dir.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return (
                "Error: create-vite failed.\n\n"
                f"STDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}"
            )
        return (
            "Scaffolded Vite + TypeScript project.\n\n"
            f"- Path: {project_dir}\n"
            f"- Command: {' '.join(cmd)}\n\n"
            "Next: run `npm install && npm run dev` inside the project."
        )

    def _scaffold_desktop(self, project_dir: Path, project_name: str, template: str | None) -> str:
        package_json = project_dir / "package.json"
        package_json.write_text(
            '{\n'
            '  "name": "' + project_name + '",\n'
            '  "private": true,\n'
            '  "version": "0.0.0",\n'
            '  "type": "module",\n'
            '  "scripts": {\n'
            '    "dev": "vite"\n'
            '  }\n'
            '}\n',
            encoding="utf-8",
        )
        index_html = project_dir / "index.html"
        index_html.write_text(
            '<!doctype html>\n'
            '<html lang="en">\n'
            '<head>\n'
            '  <meta charset="UTF-8" />\n'
            '  <title>' + project_name + '</title>\n'
            '</head>\n'
            '<body>\n'
            '  <div id="root"></div>\n'
            '  <script type="module" src="/src/main.ts"></script>\n'
            '</body>\n'
            '</html>\n',
            encoding="utf-8",
        )
        src_dir = project_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "main.ts").write_text(
            "const root = document.getElementById('root');\n"
            "if (root) root.innerHTML = '<h1>" + project_name + "</h1>';\n",
            encoding="utf-8",
        )
        return (
            "Scaffolded minimal desktop project.\n\n"
            f"- Path: {project_dir}\n"
            "Next: run `npm install && npm run dev` inside the project."
        )
