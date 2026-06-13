"""Workflow mining utilities inspired by the `/distill` workflow."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DistilledPattern:
    pattern_id: str
    name: str
    description: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "evidence": self.evidence,
            "tags": self.tags,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DistilledPattern:
        return cls(
            pattern_id=data["pattern_id"],
            name=data["name"],
            description=data.get("description", ""),
            evidence=data.get("evidence", []),
            tags=data.get("tags", []),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DistilledSkill:
    skill_id: str
    name: str
    prompt_template: str
    source_patterns: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "prompt_template": self.prompt_template,
            "source_patterns": self.source_patterns,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DistilledSkill:
        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            prompt_template=data.get("prompt_template", ""),
            source_patterns=data.get("source_patterns", []),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )


class Distiller:
    def __init__(self, storage_dir: Path | None = None) -> None:
        if storage_dir is None:
            storage_dir = Path.home() / ".teai_builder" / "distill"
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.storage_dir / f"{name}.json"

    def save_pattern(self, pattern: DistilledPattern) -> Path:
        path = self._path(pattern.pattern_id)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(pattern.to_dict(), f, indent=2)
        tmp.replace(path)
        return path

    def load_pattern(self, pattern_id: str) -> DistilledPattern | None:
        path = self._path(pattern_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return DistilledPattern.from_dict(json.load(f))

    def save_skill(self, skill: DistilledSkill) -> Path:
        path = self._path(skill.skill_id)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(skill.to_dict(), f, indent=2)
        tmp.replace(path)
        return path

    def load_skill(self, skill_id: str) -> DistilledSkill | None:
        path = self._path(skill_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return DistilledSkill.from_dict(json.load(f))

    def list_patterns(self) -> list[DistilledPattern]:
        patterns = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    patterns.append(DistilledPattern.from_dict(json.load(f)))
            except (OSError, json.JSONDecodeError):
                continue
        patterns.sort(key=lambda p: p.created_at, reverse=True)
        return patterns

    def list_skills(self) -> list[DistilledSkill]:
        skills = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    skills.append(DistilledSkill.from_dict(json.load(f)))
            except (OSError, json.JSONDecodeError):
                continue
        skills.sort(key=lambda s: s.created_at, reverse=True)
        return skills


# Global singleton
_distiller: Distiller | None = None


def get_distiller() -> Distiller:
    global _distiller
    if _distiller is None:
        _distiller = Distiller()
    return _distiller
