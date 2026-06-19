"""Adapter view for legacy Streamlit tab content still hosted in app.py."""

from __future__ import annotations


def render(ctx, tab_titles, user_role: str) -> None:
    """Render legacy tab content behind a view boundary."""

    return ctx.legacy_render_main_tab_content(tab_titles, user_role)
