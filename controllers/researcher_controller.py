"""Researcher role controller."""

from __future__ import annotations

from . import tab_controller


def render(ctx, tab_titles) -> None:
    """Render the researcher workspace through its view package."""

    return ctx.researcher_frontend.render(tab_titles, tab_controller.renderer_for(ctx))
