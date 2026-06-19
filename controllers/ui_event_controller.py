"""Controller for events emitted by the JS-backed UI shell."""

from __future__ import annotations

import streamlit as st

from backend import auth_service


def consume_rehab_ui_event(ctx, event, tab_titles=None) -> None:
    """Handle UI events from the bridge without coupling controllers to app.py."""

    if not event or not isinstance(event, dict):
        return
    event_id = event.get("id")
    if event_id and st.session_state.get("_rehab_ui_last_event_id") == event_id:
        return
    if event_id:
        st.session_state["_rehab_ui_last_event_id"] = event_id

    event_type = event.get("type")
    if event_type == "theme":
        next_theme = event.get("theme")
        if next_theme in ("light", "dark"):
            st.session_state.theme = next_theme
            ctx.rerun_toan_bo_app()
        return

    if event_type == "logout":
        ctx.dang_xuat_ve_dang_nhap()
        return

    if event_type == "tab" and tab_titles:
        target = ctx.tab_from_slug(tab_titles, event.get("tab"))
        if target:
            st.session_state.active_tab = target
            st.session_state.active_tab_widget = target
            st.session_state["inline_active_tab_widget"] = target
            ctx.sync_route_query(tab_titles=tab_titles)
            ctx.rerun_toan_bo_app()
        return

    if event_type == "side_control":
        key = str(event.get("key") or "")
        value = event.get("value")
        try:
            if key in {"ncv_confidence", "ncv_sensitivity"}:
                st.session_state[key] = max(0.0, min(1.0, float(value)))
            elif key == "ncv_skip_frames":
                parsed = int(value)
                st.session_state[key] = parsed if parsed in {0, 1, 2, 4} else 0
            elif key == "ncv_resize_width":
                parsed = int(value)
                st.session_state[key] = parsed if parsed in {480, 720, 1080} else 480
            elif key == "ncv_giai_doan":
                allowed = {
                    ctx.PHASE_UI_LABELS["g1"],
                    ctx.PHASE_UI_LABELS["g2"],
                    ctx.PHASE_UI_LABELS["g3"],
                }
                if value in allowed:
                    st.session_state[key] = ctx.normalize_phase_selection(value)
            elif key == "ncv_model_type":
                if value in {"MediaPipe Heavy", "MediaPipe Full", "MediaPipe Lite"}:
                    st.session_state[key] = value
            else:
                return
            ctx.rerun_toan_bo_app()
        except Exception as exc:
            st.session_state["_rehab_sidebar_notice"] = f"Không cập nhật được cấu hình: {exc}"
            ctx.rerun_toan_bo_app()
        return

    if event_type == "side_reset_progress":
        n_removed = ctx.clear_all_progress_files()
        for key in ("reanalyze_triggered", "view_old_analysis", "has_data", "stats", "angle_df", "current_eval_video"):
            st.session_state.pop(key, None)
        st.session_state["_rehab_sidebar_notice"] = f"Đã làm mới tiến trình - xóa {n_removed} tệp tiến trình."
        ctx.rerun_toan_bo_app()
        return

    if event_type == "admin_user_search":
        query = ctx.normalize_auth_text(event.get("username", ""))
        st.session_state["_admin_sidebar_search_query"] = query
        if not query:
            st.session_state["_admin_sidebar_search_result"] = None
            ctx.rerun_toan_bo_app()
            return
        users = ctx.load_users()
        u_key = ctx.auth_lookup_key(users, query)
        if u_key:
            rec = users.get(u_key) or {}
            st.session_state["_admin_sidebar_search_result"] = {
                "found": True,
                "username": u_key,
                "full_name": rec.get("full_name") or u_key,
                "role": rec.get("role") or "Chưa rõ",
                "email": rec.get("email") or "",
            }
        else:
            st.session_state["_admin_sidebar_search_result"] = {
                "found": False,
                "username": query,
                "message": "Không tìm thấy người dùng.",
            }
        ctx.rerun_toan_bo_app()
        return

    if event_type == "patient_create_symptom":
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else event
        if not st.session_state.get("logged_in") or not st.session_state.get("user_info"):
            st.session_state["_rehab_app_notice"] = {
                "type": "error",
                "message": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
            }
            ctx.rerun_toan_bo_app()
            return
        ok, message, record = ctx.create_patient_symptom(payload, st.session_state.get("user_info") or {})
        st.session_state["_rehab_app_notice"] = {
            "type": "success" if ok else "error",
            "message": message,
        }
        if ok and record:
            st.session_state["_rehab_last_symptom_record"] = record
        ctx.rerun_toan_bo_app()
        return

    if event_type == "demo_login":
        role = event.get("role") or "Bệnh nhân"
        ctx.dang_nhap_demo_theo_vai_tro(role)
        return

    if event_type == "forgot_password":
        st.session_state["_auth_mode"] = "forgot"
        st.session_state.pop("_auth_notice", None)
        ctx.rerun_toan_bo_app()
        return

    if event_type == "reset_password":
        st.session_state["_auth_mode"] = "forgot"
        ok, message = auth_service.reset_password(
            event.get("username", ""),
            event.get("email", ""),
            event.get("password", ""),
            event.get("password2", ""),
            load_users=ctx.load_users,
            save_users=ctx.save_users,
            lookup_user=ctx.auth_lookup_key,
            normalize_text=ctx.normalize_auth_text,
            hash_password=ctx.hash_password,
            now_fn=ctx.get_vn_now,
        )
        if ok:
            st.session_state["_auth_mode"] = "login"
        st.session_state["_auth_notice"] = {
            "kind": "success" if ok else "error",
            "message": message,
        }
        ctx.rerun_toan_bo_app()
        return

    if event_type == "login":
        ok, user_key, user_record, message = auth_service.authenticate_user(
            event.get("username", ""),
            event.get("password", ""),
            load_users=ctx.load_users,
            lookup_user=ctx.auth_lookup_key,
            verify_password=ctx.verify_auth_password,
            upgrade_password=ctx.upgrade_password_hash_if_needed,
        )
        if ok and user_key and user_record:
            st.session_state.pop("_auth_notice", None)
            st.session_state.pop("_auth_mode", None)
            ctx.hoan_tat_dang_nhap(user_key, user_record)
            ctx.rerun_toan_bo_app()
        else:
            st.session_state["_auth_notice"] = {
                "kind": "error",
                "message": message,
            }
            st.session_state["_auth_mode"] = "login"
            ctx.rerun_toan_bo_app()
        return

    if event_type == "register":
        st.session_state["_auth_mode"] = "register"
        ok, message = auth_service.register_user(
            event.get("username", ""),
            event.get("email", ""),
            event.get("password", ""),
            event.get("password2", ""),
            event.get("role") or "Bệnh nhân",
            event.get("full_name", ""),
            load_users=ctx.load_users,
            save_users=ctx.save_users,
            lookup_user=ctx.auth_lookup_key,
            normalize_text=ctx.normalize_auth_text,
            hash_password=ctx.hash_password,
            now_fn=ctx.get_vn_now,
        )
        if ok:
            st.session_state["_auth_mode"] = "login"
        st.session_state["_auth_notice"] = {
            "kind": "success" if ok else "error",
            "message": message,
        }
        ctx.rerun_toan_bo_app()
