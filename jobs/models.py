"""Small job-status model used by future worker extraction."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class JobStatus:
    id: str
    type: str
    actor: str
    status: str = "queued"
    progress: float = 0.0
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "type": self.type,
            "actor": self.actor,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
