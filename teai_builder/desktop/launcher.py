"""Stable desktop entrypoint for TeAI Builder.

This module is intended to be used as the PyInstaller script entrypoint
(`python -m teai_builder.desktop` or `pyinstaller .../launcher.py`).
"""

from __future__ import annotations

import os
import sys
import time
import webbrowser
from pathlib import Path
from threading import Thread


def _wait_for_port(port: int, timeout: float = 90.0) -> bool:
    import socket

    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect(("127.0.0.1", port))
                return True
            except OSError:
                time.sleep(0.25)
    return False


def main() -> int:
    from teai_builder.cli.commands import _run_gateway
    from teai_builder.config.loader import load_config
    from teai_builder.config.schema import Config

    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    web_dist = root / "web" / "dist"
    os.environ.setdefault("TEAI_BUILDER_WEBUI_DIR", str(web_dist))

    port = int(os.environ.get("TEAI_BUILDER_PORT", "8765"))
    url = f"http://127.0.0.1:{port}/"

    try:
        config = load_config()
    except Exception as exc:  # pragma: no cover - defensive fallback
        print(f"Desktop launcher: config load failed ({exc}). Using default config.", file=sys.stderr)
        config = Config()

    if getattr(config.agents.defaults, "workspace", None):
        workspace_path = Path(config.agents.defaults.workspace).expanduser().resolve()
    else:
        workspace_path = root / "workspace"

    if hasattr(config, "agents") and hasattr(config.agents, "defaults"):
        if not getattr(config.agents.defaults, "workspace", None):
            config.agents.defaults.workspace = str(workspace_path)

    static_dist_path = web_dist if web_dist.is_dir() else None

    gateway_thread = Thread(
        target=_run_gateway,
        args=(
            config,
            port,
            None,
            static_dist_path is not None,
            "desktop",
            {"desktop": True, "full_access": True},
            False,
        ),
        daemon=True,
    )
    gateway_thread.start()

    if not _wait_for_port(port, timeout=90.0):
        print(f"Desktop launcher: gateway did not start on port {port}", file=sys.stderr)
        return 1

    import webview

    webview.create_window(
        title="TeAi Builder",
        url=url,
        width=1280,
        height=800,
        resizable=True,
        fullscreen=False,
    )
    webview.start(debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
