"""Tab content controller.

This controller keeps role shells decoupled from the large legacy tab renderer.
Individual tabs can now move from app.py into dedicated views/controllers one at
a time without changing each role shell.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from views import legacy_tabs_view


def render(ctx, tab_titles: Sequence[str], user_role: str) -> None:
    return legacy_tabs_view.render(ctx, tab_titles, user_role)


def renderer_for(ctx) -> Callable[[Sequence[str], str], None]:
    return lambda tab_titles, user_role: render(ctx, tab_titles, user_role)
