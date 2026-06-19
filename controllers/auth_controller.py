"""Authentication controller."""

from __future__ import annotations

from views import auth_view


def render_auth(ctx) -> None:
    """Render the login/register flow through the auth view."""

    return ctx.render_auth_screen(lambda: auth_view.render(ctx))


def render_auth_view(ctx) -> None:
    """Compatibility entrypoint for legacy auth callbacks."""

    return auth_view.render(ctx)
