"""Role controllers for Admin, Patient, Doctor/KTV and Researcher workspaces."""

from __future__ import annotations

import streamlit as st

from . import admin_controller, doctor_ktv_controller, patient_controller, researcher_controller
from models.navigation import ROLE_ADMIN, ROLE_DOCTOR_KTV, ROLE_PATIENT, ROLE_RESEARCHER


ROLE_RENDERERS = {
    ROLE_PATIENT: patient_controller.render,
    ROLE_DOCTOR_KTV: doctor_ktv_controller.render,
    ROLE_RESEARCHER: researcher_controller.render,
    ROLE_ADMIN: admin_controller.render,
}


def ensure_active_tab(tab_titles) -> None:
    """Keep Streamlit tab state valid for the current role."""

    if "active_tab" not in st.session_state or st.session_state.active_tab not in tab_titles:
        st.session_state.active_tab = tab_titles[0]
    if st.session_state.get("active_tab_widget") not in tab_titles:
        st.session_state.pop("active_tab_widget", None)
        st.session_state.active_tab = tab_titles[0]


def render_role_workspace(ctx, user_role: str, tab_titles) -> None:
    """Dispatch the active role to its view package."""

    ensure_active_tab(tab_titles)
    try:
        renderer = ROLE_RENDERERS.get(user_role, patient_controller.render)
        return renderer(ctx, tab_titles)
    except Exception as tab_err:
        st.error(f"💥 Lỗi hiển thị nội dung tab: {tab_err}")
        import traceback

        st.code(traceback.format_exc())
