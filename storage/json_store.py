"""Atomic JSON storage helpers.

This module is intentionally Streamlit-free so it can be tested and reused by
scripts before the monolith is fully split.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable

_WRITE_LOCKS: dict[str, threading.Lock] = {}
_WRITE_LOCKS_GUARD = threading.Lock()


def _write_lock(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _WRITE_LOCKS_GUARD:
        lock = _WRITE_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _WRITE_LOCKS[key] = lock
        return lock


def read_json(path: str | os.PathLike[str], default: Any):
    p = Path(path)
    if not p.exists():
        return default
    with p.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path: str | os.PathLike[str], data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with _write_lock(p):
        fd, tmp_name = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            last_error: PermissionError | None = None
            for attempt in range(20):
                try:
                    os.replace(tmp_name, p)
                    last_error = None
                    break
                except PermissionError as exc:
                    last_error = exc
                    time.sleep(0.05 * (attempt + 1))
            if last_error is not None:
                with p.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                try:
                    os.remove(tmp_name)
                except OSError:
                    pass
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)


def update_json(path: str | os.PathLike[str], default: Any, update_fn: Callable[[Any], Any]):
    current = read_json(path, default)
    updated = update_fn(current)
    write_json(path, updated)
    return updated
