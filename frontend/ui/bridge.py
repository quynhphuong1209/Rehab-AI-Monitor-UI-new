"""Small Streamlit component bridge for the JavaScript UI shell.

The component is intentionally static: no Node/Vite build step is required on
Hugging Face Spaces. The iframe posts Streamlit component events back to Python,
while the visible UI is mounted into the parent document.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components


_FRONTEND_ROOT = Path(__file__).resolve().parents[1]
_component = components.declare_component("rehab_ui_shell", path=str(_FRONTEND_ROOT))


def ui_component(payload: dict[str, Any], *, key: str) -> Any:
    """Render the JS UI component and return the latest event payload."""

    return _component(payload=payload, default=None, key=key)


def emit_shell_mount(*, spacing_top: int = 72) -> None:
    """Reserve app top spacing so Streamlit content starts below the JS topbar."""

    st.markdown(
        f'<div class="rehab-js-content-anchor" style="height:{int(spacing_top)}px"></div>',
        unsafe_allow_html=True,
    )
