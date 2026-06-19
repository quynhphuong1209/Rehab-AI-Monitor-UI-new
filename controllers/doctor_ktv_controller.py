"""Doctor/KTV role controller."""

from __future__ import annotations

from . import tab_controller


def render(ctx, tab_titles) -> None:
    """Render the Doctor/KTV workspace through its view package."""

    return ctx.doctor_ktv_frontend.render(tab_titles, tab_controller.renderer_for(ctx))
