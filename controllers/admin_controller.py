"""Admin role controller."""

from __future__ import annotations

from . import tab_controller


def render(ctx, tab_titles) -> None:
    """Render the administrator workspace through its view package."""

    return ctx.admin_frontend.render(tab_titles, tab_controller.renderer_for(ctx))
