"""Legacy Streamlit sidebar view, isolated behind an MVC view boundary."""

from __future__ import annotations

import os

import streamlit as st

from models.navigation import ROLE_ADMIN, ROLE_DOCTOR_KTV, ROLE_PATIENT, ROLE_RESEARCHER


def render_system_panel(ctx) -> None:
    """Render shared system controls and sync status."""

    def update_theme_callback():
        st.session_state.theme = "dark" if st.session_state.get("theme_toggle_top", True) else "light"

    with st.sidebar:
        st.markdown('<div class="side-section">PANEL PHỤ TRỢ</div>', unsafe_allow_html=True)
        st.markdown("### 🛠️ HỆ THỐNG")

        current_theme = st.session_state.get("theme", "dark")
        label = "🌙 Chế độ Tối" if current_theme == "dark" else "☀️ Chế độ Sáng"
        desired_toggle_state = current_theme == "dark"
        if st.session_state.get("theme_toggle_top") != desired_toggle_state:
            st.session_state["theme_toggle_top"] = desired_toggle_state
        st.toggle(label, key="theme_toggle_top", on_change=update_theme_callback)

        user_info = st.session_state.user_info
        st.markdown(
            f"""
            <div style="background: rgba(255, 215, 0, 0.1); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 215, 0, 0.3); margin-top: 10px; margin-bottom: 10px;">
                <div style="font-size: 0.8rem; color: #888;">Đang đăng nhập:</div>
                <div style="color: #ffd700; font-weight: bold; font-size: 1.1rem; margin-bottom: 10px;">👤 {user_info['username']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if ctx.HF_SPACE_ID or os.path.exists("/data"):
            hf_ok, hf_msg = ctx.kiem_tra_quyen_hf_dataset()
            if hf_ok:
                sub = hf_msg or f"Dataset: <b>{ctx.HF_DATASET_ID}</b>"
                st.markdown(
                    f"""
                    <div style="background: rgba(46, 204, 113, 0.15); padding: 10px; border-radius: 8px; border: 1px solid rgba(46, 204, 113, 0.4); text-align: center; margin-top: 5px; margin-bottom: 15px;">
                        <span style="color: #2ecc71; font-weight: bold; font-size: 0.85rem;">💚 Cloud Sync: ĐÃ KÍCH HOẠT</span>
                        <p style="color: #aaa; font-size: 0.75rem; margin: 5px 0 0 0;">{sub}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif ctx.HF_TOKEN:
                lib_err = ctx.hf_la_loi_thu_vien(hf_msg or "")
                sync_label = "THƯ VIỆN CHƯA SẴN SÀNG" if lib_err else "DÙNG DỮ LIỆU LOCAL"
                st.markdown(
                    f"""
                    <div style="background: rgba(52, 152, 219, 0.15); padding: 12px; border-radius: 8px; border: 1px solid rgba(52, 152, 219, 0.35); text-align: center; margin-top: 5px; margin-bottom: 15px;">
                        <span style="color: #3498db; font-weight: bold; font-size: 0.85rem;">☁️ Cloud Sync: {sync_label}</span>
                        <p style="color: #ddd; font-size: 0.75rem; margin: 5px 0 0 0;">{hf_msg or 'Token chưa đọc được Dataset.'} App đang dùng dữ liệu local hiện có.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div style="background: rgba(52, 152, 219, 0.15); padding: 12px; border-radius: 8px; border: 1px solid rgba(52, 152, 219, 0.35); text-align: center; margin-top: 5px; margin-bottom: 15px;">
                        <span style="color: #3498db; font-weight: bold; font-size: 0.85rem;">☁️ Cloud Sync: DÙNG DỮ LIỆU LOCAL</span>
                        <p style="color: #ddd; font-size: 0.75rem; margin: 5px 0 0 0;">Chưa cấu hình <b>HF_TOKEN</b>. App vẫn đọc dữ liệu local hiện có; cấu hình token nếu cần đồng bộ Dataset.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div style="background: rgba(52, 152, 219, 0.15); padding: 10px; border-radius: 8px; border: 1px solid rgba(52, 152, 219, 0.4); text-align: center; margin-top: 5px; margin-bottom: 15px;">
                    <span style="color: #3498db; font-weight: bold; font-size: 0.85rem;">💾 Bộ nhớ: Local Storage</span>
                    <p style="color: #aaa; font-size: 0.75rem; margin: 5px 0 0 0;">Đang chạy offline trên máy tính cá nhân.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("🚪 Đăng xuất hệ thống", width="stretch", key="logout_sidebar", type="secondary"):
            ctx.dang_xuat_ve_dang_nhap()
        st.markdown("---")


def render_role_panel(ctx, user_role: str) -> None:
    """Render role-specific helper panel."""

    with st.sidebar:
        st.markdown(f"### 🎭 VAI TRÒ: {user_role.upper()}")

        if user_role == ROLE_RESEARCHER:
            _render_researcher_panel(ctx)
        elif user_role == ROLE_ADMIN:
            _render_admin_panel(ctx)
        elif user_role == ROLE_DOCTOR_KTV:
            _render_doctor_panel(ctx)
        else:
            _render_patient_panel()

        st.markdown("---")
        st.markdown("**👨‍🏫 Giảng viên hướng dẫn 1 (Khoa học dữ liệu):** TS. Trần Hồng Việt 🎓")
        st.markdown("**👩‍🏫 Giảng viên hướng dẫn 2 (Lâm sàng):** Nguyễn Thị Thùy Chi 🎓")
        st.markdown("**🏥 Trường Đại học Y tế Công cộng**")
        st.markdown("**👩‍⚕️ Chủ nhiệm đề tài:** Đinh Lê Quỳnh Phương")


def _render_researcher_panel(ctx) -> None:
    st.markdown("### 🔬 THÔNG TIN CHUYÊN GIA")
    st.markdown(
        f"""
        <div class="custom-card" style="padding: 10px; border-left: 5px solid #00c6ff; background: rgba(0, 198, 255, 0.05);">
            <p style="margin:0; font-weight:bold; color:#00c6ff;">👤 {st.session_state.user_info.get('full_name', 'Chuyên gia AI')}</p>
            <p style="margin:0; font-size:0.8rem; color:#888;">Trường Đại học Y tế Công cộng</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚙️ CẤU HÌNH AI & TỐC ĐỘ")
    st.slider("Độ tự tin tối thiểu (Confidence)", 0.0, 1.0, 0.5, key="ncv_confidence", help="Ngưỡng để AI chấp nhận một điểm khớp xương.")
    st.selectbox(
        "Tốc độ xử lý",
        options=[0, 1, 2, 4],
        index=([0, 1, 2, 4].index(st.session_state.get("ncv_skip_frames", 0)) if st.session_state.get("ncv_skip_frames", 0) in [0, 1, 2, 4] else 0),
        format_func=lambda x: "Tự động (theo độ dài video)" if x == 0 else f"Nhanh (Bỏ qua {x} frame)",
        key="ncv_skip_frames",
        help="0 = Tự động tối ưu theo độ dài video (video >100s tự bỏ frame). Chọn giá trị khác để ghi đè.",
    )
    st.selectbox(
        "Độ phân giải video (Video Quality)",
        options=[480, 720, 1080],
        index=([480, 720, 1080].index(st.session_state.get("ncv_resize_width", 720)) if st.session_state.get("ncv_resize_width", 720) in [480, 720, 1080] else 1),
        format_func=lambda x: "480p (Tốc độ tối ưu)" if x == 480 else ("720p (HD - Chuẩn sắc nét)" if x == 720 else "1080p (Full HD - Cực kỳ chuẩn xác)"),
        key="ncv_resize_width",
        help="Độ phân giải càng cao thì vẽ khung xương càng sắc nét và bám sát khớp bệnh nhân hơn.",
    )
    st.slider("Độ nhạy chuyển động (Sensitivity)", 0.0, 1.0, 0.7, key="ncv_sensitivity", help="Ảnh hưởng đến việc tính toán vận tốc khớp.")
    if "ncv_giai_doan" in st.session_state:
        st.session_state.ncv_giai_doan = ctx.normalize_phase_selection(st.session_state.ncv_giai_doan)
    st.selectbox(
        "🌱 Giai đoạn tập bệnh nhân (Mặc định video):",
        options=[ctx.PHASE_UI_LABELS["g1"], ctx.PHASE_UI_LABELS["g2"], ctx.PHASE_UI_LABELS["g3"]],
        index=1,
        key="ncv_giai_doan",
        help="Điều chỉnh ngưỡng sai số để vẽ khung xương và phát âm thanh phản hồi trực tiếp khi xử lý video.",
    )

    st.markdown("### 📊 THỐNG KÊ HỆ THỐNG")
    total_vids, pending_ai, avg_acc = ctx.thong_ke_video_nghien_cuu()
    st.markdown(
        f"""
        <div style="background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1);">
            <p style="margin:0; font-size:0.85rem; color: #aaa;">📁 Video chờ xử lý: <b style="color: #00c6ff;">{pending_ai}</b></p>
            <p style="margin:5px 0; font-size:0.85rem; color: #aaa;">🎯 Accuracy TB: <b style="color: #00ff00;">{avg_acc:.1f}%</b></p>
            <p style="margin:0; font-size:0.85rem; color: #aaa;">📚 Tổng dữ liệu: <b style="color: #ffd700;">{total_vids} Video</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎯 CHỌN MÔ HÌNH")
    st.selectbox(
        "Mô hình Pose",
        options=["MediaPipe Heavy", "MediaPipe Full", "MediaPipe Lite"],
        index=(["MediaPipe Heavy", "MediaPipe Full", "MediaPipe Lite"].index(st.session_state.get("ncv_model_type", "MediaPipe Heavy")) if st.session_state.get("ncv_model_type", "MediaPipe Heavy") in ["MediaPipe Heavy", "MediaPipe Full", "MediaPipe Lite"] else 0),
        key="ncv_model_type",
        help="Heavy (Complexity 2): chính xác nhất - mặc định. Full (Complexity 1): cân bằng tốc độ/chính xác. Lite (Complexity 0): nhanh nhất.",
    )

    st.markdown("### 🧹 LÀM MỚI TIẾN TRÌNH")
    st.caption("Hủy tất cả tiến trình đang chạy/đang chờ để bắt đầu phân tích lại từ đầu.")
    if st.button("🧹 HỦY TẤT CẢ & LÀM MỚI", key="sidebar_reset_progress", use_container_width=True, type="secondary"):
        n_removed = ctx.clear_all_progress_files()
        for key in ("reanalyze_triggered", "view_old_analysis", "has_data", "stats", "angle_df", "current_eval_video"):
            st.session_state.pop(key, None)
        st.toast(f"🧹 Đã làm mới - xóa {n_removed} tiến trình. Bạn có thể tải/phân tích lại từ đầu.", icon="✅")
        st.rerun()


def _render_admin_panel(ctx) -> None:
    st.markdown("### 👑 QUẢN TRỊ HỆ THỐNG")
    st.markdown(
        f"""
        <div style="background: rgba(255, 215, 0, 0.05); padding: 12px; border-radius: 10px; border: 1px solid rgba(255, 215, 0, 0.2); margin-bottom: 15px;">
            <p style="margin:0; font-weight:bold; color:#ffd700;">👤 {st.session_state.user_info.get('full_name', 'Administrator')}</p>
            <p style="margin:0; font-size:0.8rem; color:#888;">Quyền hạn tối cao (Super User)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        """
        **Chức năng các Tab quản trị:**
        1. **🏠 TRANG CHỦ**: Dashboard thống kê, biểu đồ và chỉ số hiệu suất hệ thống.
        2. **🛠️ QUẢN TRỊ**: Cấp tài khoản mới, xóa người dùng và reset database.
        3. **📊 NHẬT KÝ**: Xem log hoạt động chi tiết của tất cả người dùng.
        4. **📖 HƯỚNG DẪN**: Quản lý tài liệu và video hướng dẫn sử dụng.
        5. **🏥 KIẾN THỨC**: Thư viện nội dung chuyên môn về PHCN vai.
        6. **🌐 CÔNG NGHỆ**: Thông số kỹ thuật về hạ tầng AI và Computer Vision.
        """
    )
    st.markdown("### 🔍 TRA CỨU NHANH")
    q_user = st.text_input("Tìm kiếm Username", placeholder="VD: patient01")
    if q_user:
        db_u = ctx.load_users()
        if q_user in db_u:
            st.success(f"Tìm thấy: {db_u[q_user].get('full_name')} ({db_u[q_user].get('role')})")
        else:
            st.error("Không tìm thấy người dùng.")


def _render_doctor_panel(ctx) -> None:
    st.markdown("### 🩺 HỒ SƠ CHUYÊN GIA")
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(0, 198, 255, 0.1) 0%, rgba(0, 114, 255, 0.1) 100%);
                    padding: 15px; border-radius: 12px; border: 1px solid rgba(0, 198, 255, 0.2); margin-bottom: 10px;">
            <p style="margin:0; font-weight:bold; color:#00c6ff; font-size: 1.05rem;">👨‍⚕️ {st.session_state.user_info.get('full_name', 'Bác sĩ / KTV')}</p>
            <p style="margin:0; font-size:0.8rem; color:#888; margin-top: 4px;">Chuyên gia Phục hồi chức năng</p>
            <hr style="margin: 10px 0; border: 0; border-top: 1px solid rgba(0, 198, 255, 0.2);">
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #aaa;">
                <span>Cơ sở:</span>
                <span style="color: #fff;">ĐH Y tế Công cộng</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    v_list = ctx.load_danh_sach_video_nghien_cuu()
    _, e_mtime = ctx.mtimes_video_eval()
    evals_db_cached = ctx.evals_dedup_cached(e_mtime)
    evaluated_keys = {
        (e.get("patient_username"), e.get("video_name"), e.get("exercise"))
        for e in evals_db_cached
        if e.get("doctor_username") and e.get("doctor_username") != "AI_Researcher"
    }
    pending_eval = sum(
        1 for v in v_list
        if (v.get("username"), v.get("video_name"), v.get("exercise")) not in evaluated_keys
    )
    total_patients = len(set(v.get("username") for v in v_list if v.get("username")))
    st.markdown(
        f"""
        <div style="display: flex; gap: 8px; margin-bottom: 20px;">
            <div style="flex:1; background: rgba(255,255,255,0.03); padding: 12px 8px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.05);">
                <p style="margin:0; font-size: 0.65rem; color: #888; font-weight: bold;">CHỜ ĐÁNH GIÁ</p>
                <p style="margin:5px 0 0; font-size: 1.3rem; font-weight: bold; color: #ff4b4b;">{pending_eval}</p>
            </div>
            <div style="flex:1; background: rgba(255,255,255,0.03); padding: 12px 8px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.05);">
                <p style="margin:0; font-size: 0.65rem; color: #888; font-weight: bold;">TỔNG BỆNH NHÂN</p>
                <p style="margin:5px 0 0; font-size: 1.3rem; font-weight: bold; color: #00c6ff;">{total_patients}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_patient_panel() -> None:
    full_name = st.session_state.user_info.get("full_name", "Bệnh nhân")
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(0, 198, 255, 0.08) 0%, rgba(0, 114, 255, 0.08) 100%);
                    padding: 14px; border-radius: 12px; border: 1px solid rgba(0, 198, 255, 0.2); margin-bottom: 15px;">
            <p style="margin:0; font-weight:bold; color:#00c6ff; font-size: 1rem;">🏥 Xin chào, {full_name}!</p>
            <p style="margin:4px 0 0; font-size:0.8rem; color:#888;">Bệnh nhân - Hệ thống PHCN AI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### 📚 HƯỚNG DẪN SỬ DỤNG")
    st.markdown(
        """
        <div style="font-size: 0.88rem; line-height: 1.7;">
        <p>👉 Hệ thống hỗ trợ bạn qua các Tab sau:</p>
        <p>🏠 <b>TRANG CHỦ</b><br>
        <span style="color:#aaa; font-size:0.8rem;">Khai báo thông tin, triệu chứng, chọn bài tập và tải video tập luyện lên cho Bác sĩ.</span></p>
        <p>📊 <b>KẾT QUẢ ĐÁNH GIÁ</b><br>
        <span style="color:#aaa; font-size:0.8rem;">Xem nhận xét của Bác sĩ/KTV và kết quả phân tích AI về chuyển động của bạn.</span></p>
        <p>⏰ <b>LỊCH NHẮC NHỞ</b><br>
        <span style="color:#aaa; font-size:0.8rem;">Xem lịch tái khám và các nhắc nhở tập luyện hàng ngày.</span></p>
        <p>📚 <b>THÔNG TIN</b><br>
        <span style="color:#aaa; font-size:0.8rem;">Tìm hiểu về bài tập phục hồi chức năng vai và các kiến thức y tế hữu ích.</span></p>
        <p>📞 <b>LIÊN HỆ</b><br>
        <span style="color:#aaa; font-size:0.8rem;">Thông tin liên hệ với Bác sĩ/KTV khi cần hỗ trợ khẩn cấp.</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
