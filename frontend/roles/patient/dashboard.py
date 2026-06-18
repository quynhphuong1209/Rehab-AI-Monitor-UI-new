"""Patient role frontend shell."""

from __future__ import annotations

from collections.abc import Callable, Sequence

ROLE = "Bệnh nhân"


def render(
    tab_titles: Sequence[str],
    render_tab_content: Callable[[Sequence[str], str], None],
) -> None:
    """Delegate Patient tabs through a package entrypoint."""
    return render_tab_content(tab_titles, ROLE)
