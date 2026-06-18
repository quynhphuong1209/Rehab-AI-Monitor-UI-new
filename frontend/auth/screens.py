"""Authentication screen layout helpers."""

import streamlit as st


def render_auth_screen(render_impl):
    return render_impl()


def render_auth_topbar(topbar_html, *, is_light):
    if topbar_html:
        st.markdown(topbar_html(None, is_light=is_light), unsafe_allow_html=True)


def render_auth_theme_button(*, is_light):
    theme_icon = "☾" if is_light else "☀"
    if st.button(theme_icon, key="auth_theme_icon_button", help="Đổi chế độ sáng/tối"):
        st.session_state.theme = "dark" if is_light else "light"
        st.rerun()


def render_app_topbar_actions(*, is_light, on_logout):
    if st.button("↪", key="app_logout_icon_button", help="Đăng xuất"):
        on_logout()

    theme_icon = "☾" if is_light else "☀"
    if st.button(theme_icon, key="app_theme_icon_button", help="Đổi chế độ sáng/tối"):
        st.session_state.theme = "dark" if is_light else "light"
        st.rerun()


def open_auth_shell():
    st.markdown('<div class="auth-shell-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)


def close_auth_shell():
    return None


def render_auth_hero(auth_screen_html):
    if auth_screen_html:
        st.markdown(auth_screen_html(), unsafe_allow_html=True)


def render_auth_card_title():
    st.markdown(
        '<div class="auth-card-title">'
        '<h2>Đăng nhập hệ thống</h2>'
        '<p>Truy cập bảng điều khiển theo vai trò của bạn.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
