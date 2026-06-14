"""Desktop launcher/bootstrap for TeAI Builder.

This module starts the bundled backend gateway, opens the WebUI, and keeps
the gateway lifecycle tied to the desktop app window.
"""

from __future__ import annotations

import os
import sys
import time
import webbrowser
from pathlib import Path
from threading import Thread
from typing import Optional


def _wait_for_port(port: int, timeout: float = 60.0) -> bool:
    """Wait until the given TCP port is accepting connections."""
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


def _open_browser(url: str, delay: float = 1.0) -> None:
    """Open the browser after a short delay so the server can bind first."""
    time.sleep(delay)
    webbrowser.open(url)


def launch_desktop(webui_dir: Optional[Path] = None, port: int = 8765) -> int:
    """Launch the TeAI Builder desktop experience.

    Returns the exit code from the gateway process.
    """
    from teai_builder.webui.commands import start as gateway_start

    project_root = Path(__file__).resolve().parents[2]
    web_dir = webui_dir or (project_root / "web" / "dist")
    os.environ.setdefault("TEAI_BUILDER_WEBUI_DIR", str(web_dir))
    os.environ.setdefault("TEAI_BUILDER_PORT", str(port))

    url = f"http://127.0.0.1:{port}/"

    browser_thread = Thread(target=_open_browser, args=(url,), daemon=True)
    browser_thread.start()

    if hasattr(gateway_start, "app"):
        gateway_start.app()
        return 0

    return 1
