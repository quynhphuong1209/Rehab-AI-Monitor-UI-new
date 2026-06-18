"""Atomic JSON storage helpers.

This module is intentionally Streamlit-free so it can be tested and reused by
scripts before the monolith is fully split.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable


def read_json(path: str | os.PathLike[str], default: Any):
    p = Path(path)
    if not p.exists():
        return default
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | os.PathLike[str], data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_name, p)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def update_json(path: str | os.PathLike[str], default: Any, update_fn: Callable[[Any], Any]):
    current = read_json(path, default)
    updated = update_fn(current)
    write_json(path, updated)
    return updated
