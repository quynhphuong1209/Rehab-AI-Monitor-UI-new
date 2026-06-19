"""Top-level application controller."""

from __future__ import annotations

import streamlit as st

from controllers.auth_controller import render_auth
from controllers.role_controller import render_role_workspace
from controllers.ui_event_controller import consume_rehab_ui_event
from models.navigation import CLINICAL_RESEARCH_ROLES, DEFAULT_ROLE, ROLE_RESEARCHER
from views import sidebar_view


def _prepare_active_tab(ctx, tab_titles) -> None:
    if "active_tab" not in st.session_state or st.session_state.active_tab not in tab_titles:
        st.session_state.active_tab = tab_titles[0]
    if st.session_state.get("active_tab_widget") not in tab_titles:
        st.session_state.active_tab_widget = st.session_state.active_tab

    route_tab = ctx.tab_from_slug(tab_titles, ctx.query_value("tab"))
    if route_tab and route_tab != st.session_state.get("active_tab_widget"):
        st.session_state.active_tab = route_tab
        st.session_state.active_tab_widget = route_tab


def _pick_default_clinical_video(ctx, user_role: str) -> None:
    if user_role not in CLINICAL_RESEARCH_ROLES:
        return
    if st.session_state.get("current_eval_video") or st.session_state.get("_default_video_picked"):
        return
    all_vids = ctx.load_danh_sach_video_nghien_cuu()
    if all_vids:
        st.session_state.current_eval_video = all_vids[0]
    st.session_state._default_video_picked = True


def run_app(ctx) -> None:
    """Run one Streamlit pass through MVC controller boundaries."""

    ctx.thuc_hien_khoi_tao_he_thong_mot_lan()
    ctx.xu_ly_route_query_actions()
    ctx.restore_login_from_route()

    if not st.session_state.get("logged_in") or not st.session_state.get("user_info"):
        if st.session_state.get("logged_in") and not st.session_state.get("user_info"):
            st.session_state.logged_in = False
        render_auth(ctx)
        return

    ctx.poll_background_analysis_complete()

    if st.session_state.pop("_need_home_sync", False):
        ctx.dong_bo_video_list_nen(force=True)

    user_role = st.session_state.user_info.get("role", DEFAULT_ROLE)
    _pick_default_clinical_video(ctx, user_role)

    tab_titles = ctx.get_main_tab_titles_for_role(user_role)
    _prepare_active_tab(ctx, tab_titles)

    ui_event = ctx.ui_component(payload=ctx.build_rehab_ui_payload(mode="app", tab_titles=tab_titles), key="rehab_app_shell")
    consume_rehab_ui_event(ctx, ui_event, tab_titles=tab_titles)
    ctx.emit_shell_mount(spacing_top=0)
    ctx.sync_route_query(tab_titles=tab_titles)

    if user_role == ROLE_RESEARCHER:
        st.markdown('<span class="ncv-workspace-anchor"></span>', unsafe_allow_html=True)
    st.session_state["_demo_sidebar_nav_enabled"] = True
    st.session_state["_topbar_nav_enabled"] = True

    sidebar_view.render_system_panel(ctx)
    sidebar_view.render_role_panel(ctx, user_role)

    render_role_workspace(ctx, user_role, tab_titles)

    st.markdown('<div id="rehab-footer-anchor"></div>', unsafe_allow_html=True)
    ctx.hien_thi_footer_chung()
