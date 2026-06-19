"""Dependency-injected application context for MVC controllers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppContext:
    """Thin facade over legacy dependencies while app.py is being decomposed."""

    deps: Any

    def __getattr__(self, name: str) -> Any:
        try:
            return getattr(self.deps, name)
        except AttributeError as exc:
            raise AttributeError(f"AppContext is missing dependency: {name}") from exc
