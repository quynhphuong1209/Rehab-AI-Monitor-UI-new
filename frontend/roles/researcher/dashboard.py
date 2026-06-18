"""Researcher role frontend shell."""

from __future__ import annotations

from collections.abc import Callable, Sequence

ROLE = "Nghiên cứu viên"


def render(
    tab_titles: Sequence[str],
    render_tab_content: Callable[[Sequence[str], str], None],
) -> None:
    """Delegate Researcher tabs through a package entrypoint."""
    return render_tab_content(tab_titles, ROLE)
