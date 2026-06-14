"""Plugin and extension system for TeAI Builder."""

from __future__ import annotations

import importlib.util
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    entrypoint: str
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedPlugin:
    manifest: PluginManifest
    module: Any | None = None
    enabled: bool = True


class PluginSystem:
    def __init__(self, plugins_dir: Path | None = None) -> None:
        if plugins_dir is None:
            plugins_dir = Path.home() / ".teai_builder" / "plugins"
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.loaded: dict[str, LoadedPlugin] = {}

    def discover(self) -> list[PluginManifest]:
        manifests: list[PluginManifest] = []
        for path in self.plugins_dir.glob("*.py"):
            manifest = self._load_manifest(path)
            if manifest:
                manifests.append(manifest)
        return manifests

    def load_plugin(self, manifest: PluginManifest) -> LoadedPlugin:
        module_path = self.plugins_dir / f"{manifest.entrypoint}.py"
        spec = importlib.util.spec_from_file_location(manifest.plugin_id, module_path)
        module = importlib.util.module_from_spec(spec)
        if spec.loader:
            spec.loader.exec_module(module)
        loaded = LoadedPlugin(manifest=manifest, module=module)
        self.loaded[manifest.plugin_id] = loaded
        return loaded

    def _load_manifest(self, path: Path) -> PluginManifest | None:
        try:
            module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(path.stem, path))
            if module is None:
                return None
            return PluginManifest(
                plugin_id=getattr(module, "PLUGIN_ID", path.stem),
                name=getattr(module, "NAME", path.stem),
                version=getattr(module, "VERSION", "0.0.0"),
                entrypoint=getattr(module, "ENTRYPOINT", path.stem),
                description=getattr(module, "DESCRIPTION", ""),
                capabilities=getattr(module, "CAPABILITIES", []),
            )
        except Exception:
            return None
