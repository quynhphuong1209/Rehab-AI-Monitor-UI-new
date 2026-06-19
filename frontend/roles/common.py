"""Shared role dashboard helpers for the JS-backed frontend shell."""

from __future__ import annotations

from html import escape
from typing import Iterable, Sequence

import streamlit as st


def emit_role_workspace_open(role_key: str) -> None:
    st.markdown(
        f'<div class="rehab-role-workspace rehab-role-{escape(role_key, quote=True)}">',
        unsafe_allow_html=True,
    )


def emit_role_workspace_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", eyebrow: str = "", actions: Iterable[str] = ()) -> None:
    action_html = "".join(actions)
    st.markdown(
        f"""
        <section class="rehab-role-head">
          <div>
            {f'<span class="rehab-role-eyebrow">{escape(eyebrow)}</span>' if eyebrow else ''}
            <h1>{escape(title)}</h1>
            {f'<p>{escape(subtitle)}</p>' if subtitle else ''}
          </div>
          {f'<div class="rehab-role-actions">{action_html}</div>' if action_html else ''}
        </section>
        """,
        unsafe_allow_html=True,
    )


def chip(label: str, tone: str = "neutral") -> str:
    return f'<span class="rehab-status {escape(tone, quote=True)}">{escape(label)}</span>'


def metric_grid(items: Sequence[tuple[str, str, str]]) -> None:
    cards = []
    for label, value, sub in items:
        cards.append(
            "<div class=\"rehab-metric-card\">"
            f"<b>{escape(str(value))}</b>"
            f"<span>{escape(label)}</span>"
            f"{f'<small>{escape(sub)}</small>' if sub else ''}"
            "</div>"
        )
    st.markdown(f'<div class="rehab-role-metrics">{"".join(cards)}</div>', unsafe_allow_html=True)
