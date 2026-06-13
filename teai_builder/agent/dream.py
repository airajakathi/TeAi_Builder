"""Memory maintenance utilities inspired by the `/dream` workflow."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DreamRecord:
    run_id: str
    created_at: float = field(default_factory=time.time)
    summary: str = ""
    improvements: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "summary": self.summary,
            "improvements": self.improvements,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DreamRecord:
        return cls(
            run_id=data["run_id"],
            created_at=data.get("created_at", time.time()),
            summary=data.get("summary", ""),
            improvements=data.get("improvements", []),
            metadata=data.get("metadata", {}),
        )


class DreamMaintainer:
    def __init__(self, storage_dir: Path | None = None) -> None:
        if storage_dir is None:
            storage_dir = Path.home() / ".teai_builder" / "dream"
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, record: DreamRecord) -> Path:
        path = self.storage_dir / f"{record.run_id}.json"
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)
        tmp.replace(path)
        return path

    def load(self, run_id: str) -> DreamRecord | None:
        path = self.storage_dir / f"{run_id}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return DreamRecord.from_dict(json.load(f))

    def list_recent(self, limit: int = 20) -> list[DreamRecord]:
        records = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    records.append(DreamRecord.from_dict(json.load(f)))
            except (OSError, json.JSONDecodeError):
                continue
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[: max(1, limit)]


# Global singleton
_maintainer: DreamMaintainer | None = None


def get_dream_maintainer() -> DreamMaintainer:
    global _maintainer
    if _maintainer is None:
        _maintainer = DreamMaintainer()
    return _maintainer
