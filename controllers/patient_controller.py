"""Patient role controller."""

from __future__ import annotations

from . import tab_controller


def render(ctx, tab_titles) -> None:
    """Render the patient workspace through its view package."""

    return ctx.patient_frontend.render(tab_titles, tab_controller.renderer_for(ctx))
