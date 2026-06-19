"""Authentication view mounted through the JavaScript UI bridge."""

from __future__ import annotations

from controllers.ui_event_controller import consume_rehab_ui_event


def render(ctx) -> None:
    payload = ctx.build_rehab_ui_payload(mode="auth")
    event = ctx.ui_component(payload=payload, key="rehab_auth_shell")
    consume_rehab_ui_event(ctx, event)
