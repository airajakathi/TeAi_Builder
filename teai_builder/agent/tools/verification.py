"""Independent verification runner for generated projects.

Subagents self-report success; this tool actually re-runs the static/build
checks inside the project and returns a structured pass/fail result. The result
is persisted to the project state file so ``project_gate`` consumes real
evidence before allowing delivery/deploy. Designed to never block on a missing
toolchain: an unavailable checker is reported as ``skip``, not ``fail``.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from teai_builder.agent.tools.base import Tool, tool_parameters
from teai_builder.agent.tools.project_state import (
    record_verification_result,
    resolve_project_dir,
)
from teai_builder.agent.tools.schema import IntegerSchema, StringSchema, tool_parameters_schema

_MAX_FILES_PER_CHECK = 40
_SCRIPT_BLOCK_RE = re.compile(
    r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.IGNORECASE | re.DOTALL
)
# Production-readiness smells. Reported as warnings (non-blocking) so the gate
# isn't tripped by legitimate uses, but surfaced so the CEO can demand fixes.
_SMELL_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"lorem ipsum", "placeholder lorem-ipsum copy"),
    (r"\bTODO\b|\bFIXME\b", "unfinished TODO/FIXME markers"),
    (r"your[_-]?api[_-]?key|REPLACE[_-]?ME|changeme", "placeholder credentials"),
    (r"coming soon|under construction", "stub 'coming soon' content"),
)


async def _run(cmd: str, cwd: Path, timeout: int) -> tuple[int, str]:
    """Run a shell command via a login shell so PATH (node/npx) is available."""
    shell = shutil.which("bash") or "/bin/bash"
    try:
        proc = await asyncio.create_subprocess_exec(
            shell, "-lc", cmd,
            cwd=str(cwd),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except OSError as exc:
        return 127, f"failed to launch: {exc}"
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        with __import__("contextlib").suppress(Exception):
            await proc.wait()
        return 124, f"timed out after {timeout}s"
    return proc.returncode or 0, out.decode("utf-8", errors="replace")[-4000:]


def _has_tool(name: str) -> bool:
    return shutil.which(name) is not None


@tool_parameters(
    tool_parameters_schema(
        project=StringSchema(
            "Project name under projects/ or an absolute path. "
            "Optional when there is a single project.",
            nullable=True,
        ),
        timeout=IntegerSchema(
            300,
            description="Per-check timeout in seconds (default 300, max 900).",
            minimum=10,
            maximum=900,
            nullable=True,
        ),
    )
)
class RunVerificationTool(Tool):
    """Re-run static/build checks on a project and return structured results."""

    _scopes = {"core", "subagent"}

    def __init__(self, workspace: str | None = None) -> None:
        self._workspace = workspace

    @classmethod
    def create(cls, ctx: Any) -> "RunVerificationTool":
        return cls(workspace=getattr(ctx, "workspace", None))

    @property
    def name(self) -> str:
        return "run_verification"

    @property
    def description(self) -> str:
        return (
            "Independently verify a generated project by actually re-running its "
            "static and build checks (node --check on HTML/JS, tsc --noEmit, "
            "npm run build, python compile) plus production-readiness smell scans. "
            "Returns structured pass/fail JSON and records the result on the "
            "project state file so project_gate can consume it. Run this before "
            "asking project_gate to advance to qa/deliver/deploy. Unavailable "
            "toolchains are reported as 'skip', never a false failure."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters_schema  # type: ignore[attr-defined]

    async def execute(
        self,
        project: str | None = None,
        timeout: int | None = None,
        **_: Any,
    ) -> str:
        project_dir, error = resolve_project_dir(self._workspace, project)
        if project_dir is None:
            return f"run_verification error: {error}"
        per_timeout = max(10, min(900, int(timeout or 300)))

        checks: list[dict[str, Any]] = []
        checks.append(await self._check_node_syntax(project_dir, per_timeout))
        checks.append(await self._check_typescript(project_dir, per_timeout))
        checks.append(await self._check_npm_build(project_dir, per_timeout))
        checks.append(await self._check_python_compile(project_dir, per_timeout))
        warnings = self._scan_smells(project_dir)

        failed = [c for c in checks if c["status"] == "fail"]
        ran = [c for c in checks if c["status"] in ("pass", "fail")]
        status = "fail" if failed else ("pass" if ran else "inconclusive")
        result = {
            "status": status,
            "project": project_dir.name,
            "project_path": str(project_dir),
            "checks": checks,
            "warnings": warnings,
            "summary": self._summary(status, checks, warnings),
        }
        try:
            record_verification_result(project_dir, result)
        except OSError:
            pass
        return json.dumps(result, ensure_ascii=False, indent=2)

    @staticmethod
    def _summary(status: str, checks: list[dict[str, Any]], warnings: list[str]) -> str:
        passed = sum(1 for c in checks if c["status"] == "pass")
        failed = sum(1 for c in checks if c["status"] == "fail")
        skipped = sum(1 for c in checks if c["status"] == "skip")
        bits = [f"{passed} passed", f"{failed} failed", f"{skipped} skipped"]
        if warnings:
            bits.append(f"{len(warnings)} warning(s)")
        verdict = {
            "pass": "VERIFIED",
            "fail": "FAILED — fix before delivery",
            "inconclusive": "INCONCLUSIVE — no runnable checks matched this project",
        }[status]
        return f"{verdict}: " + ", ".join(bits)

    # ── individual checks ────────────────────────────────────────────────

    async def _check_node_syntax(self, project_dir: Path, timeout: int) -> dict[str, Any]:
        name = "node_syntax"
        if not _has_tool("node"):
            return {"name": name, "status": "skip", "detail": "node not installed"}
        html_files = self._collect(project_dir, "*.html")
        js_files = [
            p for p in self._collect(project_dir, "*.js")
            if "node_modules" not in p.parts and "dist" not in p.parts and "build" not in p.parts
        ]
        if not html_files and not js_files:
            return {"name": name, "status": "skip", "detail": "no standalone HTML/JS"}
        problems: list[str] = []
        checked = 0
        for html in html_files[:_MAX_FILES_PER_CHECK]:
            code = self._extract_inline_js(html)
            if not code.strip():
                continue
            checked += 1
            rc, out = await self._node_check_source(code, timeout)
            if rc != 0:
                problems.append(f"{html.name}: {out.strip()[:300]}")
        for js in js_files[:_MAX_FILES_PER_CHECK]:
            checked += 1
            rc, out = await _run(f"node --check {self._q(js)}", project_dir, timeout)
            if rc != 0:
                problems.append(f"{js.name}: {out.strip()[:300]}")
        if checked == 0:
            return {"name": name, "status": "skip", "detail": "no inline JS to check"}
        if problems:
            return {"name": name, "status": "fail", "detail": "; ".join(problems[:10])}
        return {"name": name, "status": "pass", "detail": f"{checked} file(s) parse cleanly"}

    async def _check_typescript(self, project_dir: Path, timeout: int) -> dict[str, Any]:
        name = "typescript"
        if not (project_dir / "tsconfig.json").is_file():
            return {"name": name, "status": "skip", "detail": "no tsconfig.json"}
        if not _has_tool("npx") and not (project_dir / "node_modules" / ".bin" / "tsc").exists():
            return {"name": name, "status": "skip", "detail": "tsc/npx unavailable"}
        local = project_dir / "node_modules" / ".bin" / "tsc"
        cmd = f"{self._q(local)} --noEmit" if local.exists() else "npx --no-install tsc --noEmit"
        rc, out = await _run(cmd, project_dir, timeout)
        if "could not determine executable" in out.lower() or "not found" in out.lower():
            return {"name": name, "status": "skip", "detail": "tsc not installed"}
        if rc != 0:
            return {"name": name, "status": "fail", "detail": out.strip()[-1500:]}
        return {"name": name, "status": "pass", "detail": "tsc --noEmit clean"}

    async def _check_npm_build(self, project_dir: Path, timeout: int) -> dict[str, Any]:
        name = "npm_build"
        pkg = project_dir / "package.json"
        if not pkg.is_file():
            return {"name": name, "status": "skip", "detail": "no package.json"}
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"name": name, "status": "fail", "detail": "package.json is not valid JSON"}
        scripts = data.get("scripts") if isinstance(data, dict) else None
        if not isinstance(scripts, dict) or "build" not in scripts:
            return {"name": name, "status": "skip", "detail": "no build script"}
        if not _has_tool("npm"):
            return {"name": name, "status": "skip", "detail": "npm not installed"}
        if not (project_dir / "node_modules").is_dir():
            return {
                "name": name,
                "status": "skip",
                "detail": "node_modules missing — run npm install first",
            }
        rc, out = await _run("npm run build --if-present", project_dir, timeout)
        if rc != 0:
            return {"name": name, "status": "fail", "detail": out.strip()[-1500:]}
        return {"name": name, "status": "pass", "detail": "npm run build succeeded"}

    async def _check_python_compile(self, project_dir: Path, timeout: int) -> dict[str, Any]:
        name = "python_compile"
        py_files = [
            p for p in self._collect(project_dir, "*.py")
            if "venv" not in p.parts and ".venv" not in p.parts and "node_modules" not in p.parts
        ]
        if not py_files:
            return {"name": name, "status": "skip", "detail": "no python files"}
        py = shutil.which("python3") or shutil.which("python")
        if not py:
            return {"name": name, "status": "skip", "detail": "python not installed"}
        rc, out = await _run(
            f"{self._q(Path(py))} -m compileall -q .", project_dir, timeout
        )
        if rc != 0:
            return {"name": name, "status": "fail", "detail": out.strip()[-1500:]}
        return {"name": name, "status": "pass", "detail": f"{len(py_files)} file(s) compile"}

    def _scan_smells(self, project_dir: Path) -> list[str]:
        warnings: list[str] = []
        exts = {".html", ".js", ".jsx", ".ts", ".tsx", ".css", ".py", ".md", ".json"}
        seen: set[str] = set()
        scanned = 0
        for path in project_dir.rglob("*"):
            if scanned >= 300:
                break
            if not path.is_file() or path.suffix.lower() not in exts:
                continue
            if any(part in {"node_modules", "dist", "build", ".git", ".teai_builder"} for part in path.parts):
                continue
            scanned += 1
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern, label in _SMELL_PATTERNS:
                if label in seen:
                    continue
                if re.search(pattern, text, re.IGNORECASE):
                    seen.add(label)
                    warnings.append(f"{label} (e.g. {path.name})")
        return warnings

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _collect(project_dir: Path, pattern: str) -> list[Path]:
        out: list[Path] = []
        for p in project_dir.rglob(pattern):
            if any(part in {"node_modules", "dist", "build", ".git", ".teai_builder"} for part in p.parts):
                continue
            if p.is_file():
                out.append(p)
            if len(out) >= _MAX_FILES_PER_CHECK * 2:
                break
        return out

    @staticmethod
    def _extract_inline_js(html_file: Path) -> str:
        try:
            html = html_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
        return "\n;\n".join(m.group(1) for m in _SCRIPT_BLOCK_RE.finditer(html))

    async def _node_check_source(self, code: str, timeout: int) -> tuple[int, str]:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".js", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(code)
            tmp = Path(fh.name)
        try:
            return await _run(f"node --check {self._q(tmp)}", tmp.parent, timeout)
        finally:
            tmp.unlink(missing_ok=True)

    @staticmethod
    def _q(path: Path) -> str:
        return "'" + str(path).replace("'", "'\\''") + "'"
