"""Minimal schema normalization for runtime JSON records."""
from __future__ import annotations

from typing import Any


def normalize_user(username: str, record: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(record or {})
    data.setdefault("full_name", username)
    data.setdefault("role", "Bệnh nhân")
    data.setdefault("email", "")
    return data


def normalize_video(record: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(record or {})
    data.setdefault("username", "")
    data.setdefault("full_name", data.get("username", ""))
    data.setdefault("video_name", "")
    data.setdefault("exercise", "")
    data.setdefault("accuracy", 0)
    data.setdefault("status", "")
    data.setdefault("video_path", "")
    data.setdefault("processed_path", None)
    return data


def normalize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
