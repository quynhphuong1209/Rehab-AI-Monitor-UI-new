"""Streamlit style and browser-behavior injection."""

from __future__ import annotations


def inject_app_styles(
    st,
    *,
    inject_design_system=None,
    inject_auth_nav_css=None,
    inject_streamlit_skin=None,
    inject_ncv_dashboard_css=None,
) -> None:
    """Inject the shared Streamlit CSS/JS shell styles."""
    def _inject_base_css_once():
        """Inject CSS nền mỗi lần rerun — Streamlit rebuild DOM nên cần inject lại mỗi lần."""
        st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&display=swap">
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons&display=swap">
    <style>
        html, body, .stApp, [data-testid="stMarkdownContainer"] {
            font-family: 'Be Vietnam Pro', 'Segoe UI', system-ui, sans-serif !important;
        }

        /* Ngăn ngừa hiện tượng rung lắc trang (layout shifting) khi xuất hiện/mất thanh cuộn dọc */
        html {
            overflow-y: scroll !important;
        }

        /* === TẮT BLINK/NHẤP NHÁY KHI FRAGMENT AUTO-REFRESH (CSS layer) ===
           Streamlit dùng nhiều cơ chế: data-stale, .stale class, inline opacity, animation.
           CSS dưới đây phủ tất cả các layer đã biết.                                      */

        /* 1. data-stale attribute (Streamlit 1.35+) */
        [data-stale], [data-stale="true"],
        [data-stale] *, [data-stale="true"] * {
            opacity: 1 !important;
            pointer-events: auto !important;
            visibility: visible !important;
            transition: none !important;
            animation: none !important;
        }

        /* 2. .stale CSS class (Streamlit internal React class) */
        .stale, .stale * {
            opacity: 1 !important;
            transition: none !important;
            animation: none !important;
        }

        /* 3. Override no-op tất cả keyframe animation Streamlit dùng khi running */
        @keyframes pulse      { 0%,100% { opacity: 1; } }
        @keyframes border-pulse { 0%,100% { } }
        @keyframes fadeIn     { 0%,100% { opacity: 1; } }
        @keyframes spin       { to { transform: rotate(360deg); } } /* giữ spinner hoạt động */

        /* === SHIMMER TRÊN THANH TIẾN TRÌNH ===
           ::after không bị [data-stale] * { animation: none } bắt vì * không match pseudo-elements.
           Kết quả: thanh luôn sáng-tối liên tục, không trông như đứng im dù % thay đổi chậm. */
        @keyframes _prog_shimmer {
            0%   { transform: translateX(-100%); }
            100% { transform: translateX(350%); }
        }
        .stProgress > div > div {
            position: relative !important;
            overflow: hidden !important;
        }
        .stProgress > div > div::after {
            content: '' !important;
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 30% !important; height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.22), transparent) !important;
            animation: _prog_shimmer 1.6s ease-in-out infinite !important;
            pointer-events: none !important;
        }

        /* 4. Nút bấm, toggle, tab: lock opacity=1, tắt animation, transition chỉ màu */
        button,
        [data-baseweb="button"],
        [data-baseweb="segmented-control"],
        [data-baseweb="segmented-control"] *,
        [data-testid^="stBaseButton"],
        [data-testid="stSegmentedControl"],
        [data-testid="stSegmentedControl"] *,
        [role="tab"], [role="tablist"],
        [data-testid="stSlider"] [role="slider"] {
            animation: none !important;
            opacity: 1 !important;
            transition: background-color 0.1s ease, color 0.1s ease,
                        border-color 0.1s ease !important;
        }

        /* 5. Xóa viền nhấp nháy khi Streamlit đang chạy */
        [data-running] button, [data-running] [data-baseweb], [data-running] [role="tab"],
        [data-stale]   button, [data-stale]   [data-baseweb], [data-stale]   [role="tab"] {
            animation: none !important;
            border-color: inherit !important;
            box-shadow: none !important;
            opacity: 1 !important;
            transition: none !important;
        }

        /* 6. Fragment container & mọi con cháu không được fade khi fragment refresh */
        [data-fragment-id], [data-fragment-id] * {
            opacity: 1 !important;
            transition: none !important;
            animation-duration: 0s !important;
        }

        /* 7. Ngăn toàn bộ giao diện blink khi rerun */
        .stApp > * { transition: none !important; }

        /* Khống chế kích thước ảnh frame để tránh giật/rung lắc giao diện khi load ảnh */
        div[data-testid="stImage"] {
            min-height: 180px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stImage"] img {
            height: 180px !important;
            object-fit: contain !important;
            background-color: rgba(128, 128, 128, 0.05) !important;
            border-radius: 8px !important;
        }

        /* === ĐẢM BẢO HỆ THỐNG STREAMLIT (HEADER, FOOTER, MENU) LUÔN HIỂN THỊ === */
        header[data-testid="stHeader"], 
        footer, 
        #MainMenu, 
        [data-testid="stToolbar"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        /* ĐẨY GIAO DIỆN XUỐNG ĐỂ KHÔNG BỊ HEADER ĐÈ LÊN NẾU CẦN */
        [data-testid="stAppViewBlockContainer"] {
            padding-top: 0 !important;
        }

        /* Tối ưu hóa giao diện st.segmented_control thành tab bar */
        .st-key-active_tab_widget,
        div[data-testid="stSegmentedControl"],
        div[data-testid="stButtonGroup"] {
            position: relative !important;
            background: transparent !important; /* Xóa nền container */
            border: none !important; /* Xóa viền bao ngoài container */
            border-bottom: none !important;
            box-shadow: none !important;
            margin-bottom: -3px !important; /* Kéo nội dung bên dưới lên gần hơn, chừa chỗ cho thanh cuộn mỏng */
            padding: 0px 5px 0px 5px !important; /* Thu nhỏ padding khi không còn mũi tên */
            width: 100% !important;
            overflow: visible !important;
        }

        /* Thiết lập flexbox không xuống dòng và cho phép cuộn ngang cho container thực sự chứa nút */
        .st-key-active_tab_widget [role="radiogroup"],
        .st-key-active_tab_widget [role="group"],
        div[data-testid="stSegmentedControl"] [role="radiogroup"],
        div[data-testid="stSegmentedControl"] [role="group"],
        div[data-testid="stButtonGroup"] [role="radiogroup"],
        div[data-testid="stButtonGroup"] [role="group"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            justify-content: flex-start !important;
            gap: 8px !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            width: 100% !important;
            scrollbar-width: thin !important; /* Firefox: thanh cuộn mỏng */
            scrollbar-color: #0072ff rgba(255, 255, 255, 0.05) !important; /* Firefox màu thanh cuộn */
            border: none !important;
            border-bottom: none !important;
            box-shadow: none !important;
        }

        /* Thiết kế thanh cuộn ngang mỏng và hiện đại cho WebKit (Chrome, Safari, Edge) */
        .st-key-active_tab_widget [role="radiogroup"]::-webkit-scrollbar,
        .st-key-active_tab_widget [role="group"]::-webkit-scrollbar,
        div[data-testid="stSegmentedControl"] [role="radiogroup"]::-webkit-scrollbar,
        div[data-testid="stSegmentedControl"] [role="group"]::-webkit-scrollbar,
        div[data-testid="stButtonGroup"] [role="radiogroup"]::-webkit-scrollbar,
        div[data-testid="stButtonGroup"] [role="group"]::-webkit-scrollbar {
            height: 5px !important; /* Rất mỏng và tinh tế */
            display: block !important;
        }
    
        .st-key-active_tab_widget [role="radiogroup"]::-webkit-scrollbar-track,
        div[data-testid="stSegmentedControl"] [role="radiogroup"]::-webkit-scrollbar-track,
        div[data-testid="stButtonGroup"] [role="radiogroup"]::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.03) !important;
            border-radius: 10px !important;
        }
    
        .st-key-active_tab_widget [role="radiogroup"]::-webkit-scrollbar-thumb,
        div[data-testid="stSegmentedControl"] [role="radiogroup"]::-webkit-scrollbar-thumb,
        div[data-testid="stButtonGroup"] [role="radiogroup"]::-webkit-scrollbar-thumb {
            background: linear-gradient(90deg, #00c6ff, #0072ff) !important;
            border-radius: 10px !important;
        }

        .st-key-active_tab_widget button,
        div[data-testid="stSegmentedControl"] button,
        div[data-testid="stButtonGroup"] button {
            border-radius: 8px 8px 0 0 !important; /* Bo góc trên, dưới phẳng để giống tab thật */
            font-weight: 600 !important;
            transition: background 0.12s ease, color 0.12s ease, border-color 0.12s ease !important;
            padding: 8px 16px !important; /* Giảm padding cho gọn */
            min-height: 38px !important;
            margin-right: 5px !important;
            border-bottom: 2px solid transparent !important; /* Viền chân mặc định trong suốt */
            min-width: max-content !important;
            max-width: none !important;
            flex-shrink: 0 !important;
            white-space: nowrap !important;
            background: rgba(255, 255, 255, 0.05) !important;
            color: rgba(255, 255, 255, 0.7) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        .st-key-active_tab_widget button p,
        div[data-testid="stSegmentedControl"] button p,
        div[data-testid="stButtonGroup"] button p,
        .st-key-active_tab_widget button div,
        div[data-testid="stSegmentedControl"] button div,
        div[data-testid="stButtonGroup"] button div,
        .st-key-active_tab_widget button span,
        div[data-testid="stSegmentedControl"] button span,
        div[data-testid="stButtonGroup"] button span {
            font-size: 1.0rem !important; /* Tăng kích thước chữ cho dễ đọc */
            font-weight: 600 !important;
            text-transform: uppercase !important;
        }
    
        /* Trạng thái được chọn (Active) */
        .st-key-active_tab_widget [aria-pressed="true"],
        .st-key-active_tab_widget [aria-checked="true"],
        .st-key-active_tab_widget [aria-selected="true"],
        .st-key-active_tab_widget [data-checked="true"],
        .st-key-active_tab_widget [class*="selected"],
        .st-key-active_tab_widget [class*="active"],
        .st-key-active_tab_widget button[data-testid*="Active"],
        .st-key-active_tab_widget button[kind*="Active"],
        div[data-testid="stSegmentedControl"] [aria-pressed="true"],
        div[data-testid="stSegmentedControl"] [aria-checked="true"],
        div[data-testid="stSegmentedControl"] [aria-selected="true"],
        div[data-testid="stSegmentedControl"] [data-checked="true"],
        div[data-testid="stSegmentedControl"] button[data-testid*="Active"],
        div[data-testid="stSegmentedControl"] button[kind*="Active"],
        div[data-testid="stButtonGroup"] [aria-pressed="true"],
        div[data-testid="stButtonGroup"] [aria-checked="true"],
        div[data-testid="stButtonGroup"] [aria-selected="true"],
        div[data-testid="stButtonGroup"] [data-checked="true"],
        div[data-testid="stButtonGroup"] button[data-testid*="Active"],
        div[data-testid="stButtonGroup"] button[kind*="Active"] {
            background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important;
            color: white !important;
            border: 1px solid #00c6ff !important;
            border-bottom: 2px solid #ff4b4b !important; /* Gạch đỏ dưới chân tab được chọn */
            box-shadow: 0 2px 8px rgba(0, 198, 255, 0.3) !important;
        }

        /* === GLOBAL TEXT RESIZING FOR BETTER READABILITY === */
        .stMarkdown p, 
        .stMarkdown li,
        .stMarkdown span,
        span[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] p,
        .stMarkdown ul,
        .stMarkdown ol,
        p,
        label {
            font-size: 1.05rem !important;
            line-height: 1.6 !important;
        }
    
        .stMarkdown h1 {
            font-size: 1.85rem !important;
        }
        .stMarkdown h2 {
            font-size: 1.55rem !important;
        }
        .stMarkdown h3 {
            font-size: 1.48rem !important; /* Tăng kích thước chữ đề mục lên một chút */
            margin-top: 10px !important; /* Thu hẹp khoảng cách phía trên */
            margin-bottom: 8px !important;
        }
        .stMarkdown h4 {
            font-size: 1.15rem !important;
        }
    
        div[data-testid="stWidgetLabel"] p {
            font-size: 1.02rem !important;
        }
    
        [data-testid="stTable"] th {
            font-size: 0.98rem !important;
            padding: 6px 12px !important;
        }
        [data-testid="stTable"] td {
            font-size: 0.98rem !important;
            padding: 6px 12px !important;
        }
    
        .stSelectbox div[role="combobox"] {
            font-size: 1.05rem !important;
            min-height: 42px !important;
        }
        .stTextInput input, .stTextArea textarea, .stNumberInput input {
            font-size: 1.05rem !important;
        }

        .stButton button, .stDownloadButton button, [data-testid="stBaseButton-secondary"],
        [data-testid="stFormSubmitButton"] button, [data-testid="stBaseButton-primary"] {
            padding: 0.35rem 1.25rem !important;
        }
        .stButton button p, .stDownloadButton button p, [data-testid="stBaseButton-secondary"] p, [data-testid="stFormSubmitButton"] button p {
            font-size: 1.0rem !important;
        }
    
        /* === STYLE HEADER & NÚT BẤM THÍCH ỨNG THEO CHỦ ĐỀ (THEME-AWARE) === */
        [data-testid="stHeader"] {
            background-color: var(--background-color) !important;
            border-bottom: 1px solid rgba(128, 128, 128, 0.1) !important;
            color: var(--text-color) !important;
        }

        /* Style các nút hệ thống (Sidebar toggle, Toolbar, Menu) */
        [data-testid="stToolbar"] button,
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stExpandSidebarButton"] button {
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            border-radius: 8px !important;
            background: rgba(128, 128, 128, 0.05) !important;
            color: var(--text-color) !important;
            padding: 4px 10px !important;
            margin-left: 5px !important;
            transition: all 0.2s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            height: 32px !important;
        }

        .stMarkdown h1.app-title,
        .stMarkdown h1.app-title *,
        .stMarkdown .main-header h1,
        .stMarkdown .main-header h1 *,
        h1.app-title,
        h1.app-title *,
        .main-header h1,
        .main-header h1 * {
            font-size: 38px !important; /* Cỡ chữ mặc định vừa vặn cho máy tính */
            line-height: 1.15 !important;
            font-weight: 850 !important; /* Độ dày cân đối */
            text-transform: uppercase !important;
            letter-spacing: -0.01em !important; /* Khôi phục khoảng cách chữ bình thường */
            word-spacing: normal !important; /* Khôi phục khoảng cách từ bình thường */
            white-space: normal !important;
            word-break: normal !important;
            display: block !important;
            text-align: center !important;
            margin-bottom: 0.3rem !important;
        }

        /* Ẩn icon liên kết tự động của Streamlit trên tiêu đề */
        a.header-anchor,
        .header-anchor,
        [data-testid="stHeaderActionElements"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
        }


        [data-testid="stToolbar"] button:hover,
        [data-testid="stSidebarCollapseButton"] button:hover,
        [data-testid="stExpandSidebarButton"] button:hover {
            background: rgba(128, 128, 128, 0.1) !important;
            border-color: rgba(128, 128, 128, 0.3) !important;
            transform: translateY(-1px);
        }

        /* Đảm bảo icon bên trong nút đổi màu theo theme */
        [data-testid="stToolbar"] button svg,
        [data-testid="stSidebarCollapseButton"] button svg,
        [data-testid="stExpandSidebarButton"] button svg {
            fill: var(--text-color) !important;
        }

        /* FIX TRIỆT ĐỂ LỖI HIỆN NHIỀU NÚT "CHỌN VIDEO" */
        [data-testid="stFileUploader"] button {
            display: none !important; /* Ẩn mặc định tất cả các nút rác bên trong uploader */
        }

        /* Chỉ hiện duy nhất nút "Duyệt file" chính và vẽ lại nó */
        [data-testid="stFileUploader"] section button[data-testid="stBaseButton-secondary"] {
            display: block !important;
            color: transparent !important;
            text-indent: -9999px !important;
            overflow: hidden !important;
            position: relative !important;
            background: #0072ff !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
            min-width: 150px !important;
            margin: 0 auto !important;
        }

        [data-testid="stFileUploader"] section button[data-testid="stBaseButton-secondary"]::after {
            content: "📂 Chọn Video" !important;
            text-indent: 0 !important;
            position: absolute !important;
            left: 50% !important;
            top: 50% !important;
            transform: translate(-50%, -50%) !important;
            color: white !important;
            font-size: 14px !important;
            font-weight: bold !important;
            visibility: visible !important;
            width: 100% !important;
            text-align: center !important;
        }

        /* Đảm bảo nút xóa (X) vẫn hiển thị nếu cần, hoặc ẩn hẳn nếu muốn sạch sẽ */
        [data-testid="stFileUploaderDeleteBtn"] {
            display: none !important; 
        }

        /* Đảm bảo các biểu tượng Material của Streamlit hiển thị bình thường */
        [data-testid="stIconMaterial"], 
        .stIconMaterial, 
        span[data-testid="stIconMaterial"] {
            display: inline-block !important;
            visibility: visible !important;
            /* Dùng đúng font Streamlit mặc định (Material Symbols Rounded) để icon ligature render đúng */
            font-family: 'Material Symbols Rounded' !important;
            font-feature-settings: "liga" 1 !important;
            -webkit-font-feature-settings: "liga" 1 !important;
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 !important;
            text-rendering: optimizeLegibility !important;
            -webkit-font-smoothing: antialiased !important;
        }

        /* Đã chuyển styling container vào các block theme-aware phía dưới */

    
        /* Đã chuyển styling input vào các block theme-aware phía dưới để tránh lỗi tàng hình chữ trong Light Mode */

    
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            overflow-x: auto;
            scroll-behavior: auto !important;
        }

        .stTabs [data-baseweb="tab"],
        .stTabs [data-baseweb="tab-panel"],
        [data-testid="stSegmentedControl"] button,
        [data-testid="stButtonGroup"] button {
            transition: none !important;
            animation: none !important;
        }

        /* Đã chuyển styling tab vào các block theme-aware phía dưới để tránh lỗi tàng hình chữ trong Light Mode */


        .stTabs [data-baseweb="tab"] div,
        .stTabs [data-baseweb="tab"] p {
            font-size: 0.85rem !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 6px !important;
            font-weight: 600 !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important;
            border: 1px solid #00c6ff !important;
            box-shadow: 0 0 15px rgba(0, 198, 255, 0.4);
        }

        /* ĐẨY GIAO DIỆN LÊN CAO TỐI ĐA */
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 10rem !important; /* Thêm khoảng trống cuối trang để kéo xuống hết cỡ */
        }
    
        /* ĐÃ LOẠI BỎ CSS OVERRIDE ĐỂ TRÁNH TRÙNG LẶP VÀ DÍU DÍU CHỮ */
        .main-header {
            text-align: center !important;
            margin-top: 0 !important;
            margin-bottom: 1.8rem !important;
            width: 100% !important;
            max-width: 100% !important;
            margin-left: auto !important;
            margin-right: auto !important;
            overflow: visible !important;
        }
        @keyframes header-logo-glow {
            0%, 100% {
                box-shadow: 0 0 12px rgba(0, 198, 255, 0.7), 0 0 0 3px rgba(0, 198, 255, 0.5);
                border-color: rgba(0, 198, 255, 0.9);
            }
            50% {
                box-shadow: 0 0 28px rgba(0, 230, 255, 1), 0 0 55px rgba(0, 198, 255, 0.4), 0 0 0 4px rgba(0, 230, 255, 0.85);
                border-color: rgba(0, 230, 255, 1);
            }
        }
        @keyframes header-logo-glow-green {
            0%, 100% {
                box-shadow: 0 0 12px rgba(0, 230, 118, 0.7), 0 0 0 3px rgba(0, 230, 118, 0.5);
                border-color: rgba(0, 230, 118, 0.9);
            }
            50% {
                box-shadow: 0 0 28px rgba(0, 255, 130, 1), 0 0 55px rgba(0, 230, 118, 0.4), 0 0 0 4px rgba(0, 255, 130, 0.85);
                border-color: rgba(0, 255, 130, 1);
            }
        }
        .main-header .header-logos-row {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 32px;
            margin: 0 auto 14px auto;
            max-width: 520px;
            padding: 10px 8px 4px 8px;
            overflow: visible;
        }
        .main-header .header-logo-glow {
            width: 82px;
            height: 82px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.92);
            padding: 3px;
            border: 3px solid rgba(0, 198, 255, 0.9);
            box-shadow: 0 0 12px rgba(0, 198, 255, 0.7), 0 0 0 3px rgba(0, 198, 255, 0.5);
            animation: header-logo-glow 2.5s ease-in-out infinite !important;
            flex-shrink: 0;
        }
        .main-header .header-logo-ds {
            animation-delay: 0.35s !important;
        }
        .main-header .header-logo-pnt {
            border-color: rgba(0, 230, 118, 0.9);
            box-shadow: 0 0 12px rgba(0, 230, 118, 0.7), 0 0 0 3px rgba(0, 230, 118, 0.5);
            animation: header-logo-glow-green 2.5s ease-in-out infinite !important;
            animation-delay: 0.7s !important;
        }
        .main-header .header-logo-glow img {
            width: 72px;
            height: 72px;
            border-radius: 50%;
            object-fit: contain;
            display: block;
        }

        .main-header p {
            font-size: clamp(0.95rem, 2vw, 1.15rem) !important;
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
        }
        .research-badge {
            margin-top: 0.4rem !important;
            margin-bottom: 0.4rem !important;
        }
        .research-badge span {
            font-size: clamp(0.75rem, 1.8vw, 0.85rem) !important;
            display: inline-block;
            max-width: 100%;
            padding: 4px 12px !important;
        }

        .google-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
            color: #444;
            padding: 12px;
            border-radius: 12px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            border: none;
            width: 100%;
            margin-top: 10px;
        }
    
        /* CUSTOM CARD ĐỂ DÙNG CHUNG */
        .custom-card {
            padding: 1.2rem;
            border-radius: 16px;
            text-align: center;
            border: 1px solid #2a5298;
        }
    
        .google-btn:hover {
            background: #f1f1f1;
            box-shadow: 0 5px 15px rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        /* === BẢNG CHỈ SỐ NGHIÊN CỨU - THÍCH ỨNG THEO THEME === */
        .research-table-container {
            padding: 1.5rem;
            border-radius: 18px;
            border: 1px solid rgba(100, 116, 139, 0.2);
            background: var(--secondary-background-color);
            transition: all 0.3s ease;
        }
    
        /* Khi ở chế độ sáng */
        @media (prefers-color-scheme: light) {
            .research-table-container {
                background: white !important;
                border: 1px solid black !important;
                color: black !important;
            }
            .research-table-container table {
                color: black !important;
            }
            .research-table-container tr {
                border-bottom: 1px solid black !important;
            }
            .research-table-container thead {
                background: #f8f9fa !important;
            }
        }

        /* === ÉP MÀU NÚT BẤM LUÔN CÓ CHỮ TRẮNG (DÙ LÀ THEME SÁNG HAY TỐI) === */
        .stButton button, .stDownloadButton button, [data-testid="stBaseButton-secondary"],
        [data-testid="stFormSubmitButton"] button, [data-testid="stBaseButton-primary"] {
            color: white !important;
            background: linear-gradient(135deg, #0072ff 0%, #00c6ff 100%) !important;
            border: none !important;
            border-radius: 30px !important; /* Bo tròn pill-shape như ảnh BN gửi */
            padding: 0.5rem 2rem !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1) !important;
        }
    
        .stButton button:hover, .stDownloadButton button:hover, [data-testid="stBaseButton-secondary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 198, 255, 0.4) !important;
            background: linear-gradient(135deg, #0056b3 0%, #00c6ff 100%) !important;
            color: white !important;
        }

        /* Chặn flash trắng khi bấm / focus nút */
        .stButton button:active,
        .stButton button:focus,
        .stButton button:focus-visible,
        .stDownloadButton button:active,
        .stDownloadButton button:focus,
        .stDownloadButton button:focus-visible,
        [data-testid="stBaseButton-primary"]:active,
        [data-testid="stBaseButton-primary"]:focus,
        [data-testid="stBaseButton-primary"]:focus-visible,
        [data-testid="stFormSubmitButton"] button:active,
        [data-testid="stFormSubmitButton"] button:focus,
        [data-testid="stFormSubmitButton"] button:focus-visible {
            background: linear-gradient(135deg, #004494 0%, #0099cc 100%) !important;
            color: #ffffff !important;
            outline: none !important;
            box-shadow: 0 2px 8px rgba(0, 198, 255, 0.35) !important;
            transform: none !important;
        }
        .stButton button[kind="secondary"]:active,
        .stButton button[kind="secondary"]:focus,
        .stButton button[kind="secondary"]:focus-visible,
        [data-testid="stBaseButton-secondary"]:active,
        [data-testid="stBaseButton-secondary"]:focus,
        [data-testid="stBaseButton-secondary"]:focus-visible {
            background: rgba(255, 255, 255, 0.16) !important;
            color: #ffffff !important;
            border-color: rgba(0, 198, 255, 0.45) !important;
            outline: none !important;
        }
        .stButton button:active p,
        .stButton button:focus p,
        .stDownloadButton button:active p,
        .stDownloadButton button:focus p {
            color: #ffffff !important;
        }

        /* Nút secondary — tách khỏi primary để bấm đúng vai trò */
        .stButton button[kind="secondary"],
        [data-testid="stBaseButton-secondary"] {
            background: rgba(255, 255, 255, 0.08) !important;
            color: #e8e8e8 !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            box-shadow: none !important;
        }
        .stButton button[kind="secondary"]:hover,
        [data-testid="stBaseButton-secondary"]:hover {
            background: rgba(255, 255, 255, 0.14) !important;
            color: #ffffff !important;
        }

        /* Sửa nút bị mờ/không bấm được khi Streamlit rerun */
        .stButton > button:not(:disabled),
        .stDownloadButton > button:not(:disabled),
        [data-testid="stBaseButton-primary"]:not(:disabled),
        [data-testid="stBaseButton-secondary"]:not(:disabled),
        [data-testid="stFormSubmitButton"] button:not(:disabled) {
            pointer-events: auto !important;
            cursor: pointer !important;
            opacity: 1 !important;
            position: relative !important;
            z-index: 2 !important;
        }
        .stApp[data-test-script-state="running"] .stButton > button:not(:disabled),
        .stApp[data-test-script-state="running"] [data-testid="stBaseButton-primary"]:not(:disabled),
        .stApp[data-test-script-state="running"] [data-testid="stBaseButton-secondary"]:not(:disabled) {
            pointer-events: auto !important;
            opacity: 1 !important;
        }

        /* Đảm bảo chữ bên trong không bị đổi màu bởi Streamlit default */
        .stButton button p, .stDownloadButton button p {
            color: white !important;
        }

        /* Giới hạn kích cỡ video toàn hệ thống (mức vừa/nhỏ) */
        video {
            max-width: 680px !important;
            max-height: 480px !important;
            width: 100% !important;
            height: auto !important;
            margin: 0 auto !important;
            display: block !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.45) !important;
            object-fit: contain !important;
        }

        /* ===== CUSTOM SCROLLBAR - CHỈ ÁP DỤNG TRONG APP (KHÔNG ẢNH HƯỞNG CHROME/FIREFOX) ===== */
        /* Webkit (Chrome, Edge, Safari) - dùng các thẻ cụ thể để tránh ghi đè browser scrollbar */
        .stApp ::-webkit-scrollbar,
        [data-testid="stAppViewContainer"] ::-webkit-scrollbar,
        [data-testid="stSidebar"] ::-webkit-scrollbar,
        .main ::-webkit-scrollbar,
        [data-testid="stVerticalBlock"] ::-webkit-scrollbar,
        textarea::-webkit-scrollbar {
            width: 6px !important;
            height: 6px !important;
        }

        .stApp ::-webkit-scrollbar-track,
        [data-testid="stAppViewContainer"] ::-webkit-scrollbar-track,
        [data-testid="stSidebar"] ::-webkit-scrollbar-track,
        .main ::-webkit-scrollbar-track,
        [data-testid="stVerticalBlock"] ::-webkit-scrollbar-track,
        textarea::-webkit-scrollbar-track {
            background: transparent !important;
            border-radius: 10px !important;
        }

        .stApp ::-webkit-scrollbar-thumb,
        [data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb,
        [data-testid="stSidebar"] ::-webkit-scrollbar-thumb,
        .main ::-webkit-scrollbar-thumb,
        [data-testid="stVerticalBlock"] ::-webkit-scrollbar-thumb,
        textarea::-webkit-scrollbar-thumb {
            border-radius: 10px !important;
            border: 2px solid transparent !important;
            background-clip: padding-box !important;
        }

        .stApp ::-webkit-scrollbar-corner,
        [data-testid="stAppViewContainer"] ::-webkit-scrollbar-corner {
            background: transparent !important;
        }

        /* GIẢM KÍCH CỠ CHỮ TRONG SIDEBAR THEO YÊU CẦU */
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown li,
        [data-testid="stSidebar"] .stMarkdown span,
        [data-testid="stSidebar"] span[data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] li,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div[data-testid="stWidgetLabel"] p {
            font-size: 0.88rem !important;
            line-height: 1.5 !important;
        }
        [data-testid="stSidebar"] h1 {
            font-size: 1.4rem !important;
        }
        [data-testid="stSidebar"] h2 {
            font-size: 1.25rem !important;
        }
        [data-testid="stSidebar"] h3 {
            font-size: 1.15rem !important;
            margin-top: 8px !important;
            margin-bottom: 6px !important;
        }
        [data-testid="stSidebar"] h4 {
            font-size: 1.0rem !important;
        }
        [data-testid="stSidebar"] .stSelectbox div[role="combobox"] {
            font-size: 0.88rem !important;
            min-height: 36px !important;
        }
        [data-testid="stSidebar"] .stTextInput input, 
        [data-testid="stSidebar"] .stTextArea textarea, 
        [data-testid="stSidebar"] .stNumberInput input {
            font-size: 0.88rem !important;
        }
        [data-testid="stSidebar"] .stButton button,
        [data-testid="stSidebar"] .stDownloadButton button,
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            padding: 0.25rem 1.0rem !important;
        }
        [data-testid="stSidebar"] .stButton button p,
        [data-testid="stSidebar"] .stDownloadButton button p,
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
            font-size: 0.85rem !important;
        }
        [data-testid="stSidebar"] div[data-testid="stAlert"] * {
            font-size: 0.85rem !important;
        }
    </style>
    """, unsafe_allow_html=True)


    _inject_base_css_once()

    # Inject JS chặn blink qua components.v1.html — không bị st.markdown strip script tags
    import streamlit.components.v1 as _st_components
    _st_components.html("""<script>
    (function(){
        if(window.__stNoBlinkInstalled)return;
        window.__stNoBlinkInstalled=true;
        // Fix bất kỳ element nào bị giảm opacity hoặc có transition opacity
        function fixEl(el){
            if(!el||el.nodeType!==1)return;
            var st=el.style;
            if(!st)return;
            var op=parseFloat(st.opacity);
            if(op>0&&op<0.99){
                st.setProperty('opacity','1','important');
                st.setProperty('transition','none','important');
            }
            // Xóa transition opacity trên mọi element
            if(st.transition&&st.transition.indexOf('opacity')>-1){
                st.setProperty('transition','none','important');
            }
        }
        function fixTree(root){
            if(!root||root.nodeType!==1)return;
            fixEl(root);
            var all=root.querySelectorAll?root.querySelectorAll('*'):[];
            for(var i=0;i<all.length;i++)fixEl(all[i]);
        }
        var obs=new MutationObserver(function(muts){
            for(var i=0;i<muts.length;i++){
                var m=muts[i];
                if(m.type==='attributes'){
                    if(m.attributeName==='style'||m.attributeName==='class')fixEl(m.target);
                } else if(m.type==='childList'){
                    for(var j=0;j<m.addedNodes.length;j++)fixTree(m.addedNodes[j]);
                }
            }
        });
        function start(){
            if(!document.body){setTimeout(start,50);return;}
            obs.observe(document.body,{attributes:true,attributeFilter:['style','class'],childList:true,subtree:true});
            try{
                var p=window.parent;
                if(p&&p.document&&p.document.body)
                    obs.observe(p.document.body,{attributes:true,attributeFilter:['style','class'],childList:true,subtree:true});
            }catch(e){}
        }
        start();
    })();
    </script>""", height=0, scrolling=False)

    # === CSS CHO CHẾ ĐỘ TỐI (DARK MODE FORCED) ===
    # Ép giao diện luôn tối kể cả khi Chrome/Hệ thống đang ở chế độ Sáng
    # Inject mỗi rerun — DOM được rebuild nên cần inject lại
    _current_theme = st.session_state.get('theme', 'dark')
    _last_injected_theme = st.session_state.get('_last_injected_theme', '')
    if st.session_state.get('theme', 'dark') == 'dark':
        st.markdown("""
        <style>
            /* Khai báo hệ màu tối cho toàn bộ trình duyệt - Đã loại bỏ color-scheme để k ảnh hưởng Chrome */
            html, body {
                caret-color: white !important; /* Đảm bảo con trỏ luôn sáng */
            }
        
            /* ÉP CON TRỎ GÕ CHỮ TRÊN TẤT CẢ PHẦN TỬ */
            * {
                caret-color: white !important;
            }
        
            /* Chỉnh màu khi bôi đen văn bản */
            ::selection {
                background-color: #2a5298 !important;
                color: white !important;
            }

            /* Ép nền ứng dụng (ĐÃ TẮT THEO YÊU CẦU) */
            /*
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainViewContainer"] {
                background-color: #0d0d1a !important;
                color: white !important;
            }
            */
        
            /* Ép nền Sidebar (ĐÃ TẮT THEO YÊU CẦU) */
            /*
            [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
                background-color: #1a1a2e !important;
            }
            */
        
            /* Ép nền Header trong suốt (ĐÃ CHUYỂN RA NGOÀI ĐỂ TỰ ĐỘNG THEO THEME) */
        
            /* Đảm bảo văn bản luôn trắng trong chế độ tối (Chỉ áp dụng khi session_state là dark) */
            .stMarkdown, p, span, label, h1, h2, h3, h4, li, div, small {
                color: #ffffff !important;
                text-shadow: none !important;
            }
        
            /* Đảm bảo văn bản luôn trắng trong chế độ tối */
            .stMarkdown, p, span, label, h1, h2, h3, h4, li, div, small {
                color: #ffffff !important;
                text-shadow: none !important;
            }
        
            /* ĐỒNG BỘ HÓA HÌNH DÁNG (KHÔNG ĐỔI MÀU) THEO BANNER */
            /* CHỈ BO GÓC Ô NHẬP LIỆU - KHÔNG BO GÓC NHÃN TIÊU ĐỀ */
            /* KHỬ VIỀN KHUNG BAO NGOÀI CỦA CÁC Ô THÔNG BÁO (INFO, SUCCESS, WARNING) */
            [data-testid="stNotification"], 
            [data-testid="stNotification"] > div {
                border: none !important;
                box-shadow: none !important;
                border-radius: 12px !important;
            }

            /* PHỤC HỒI KHUÔN HÌNH CHUẨN (BO GÓC & VIỀN MẢNH) */
            [data-testid="stExpander"] {
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 12px !important;
                background-color: rgba(255, 255, 255, 0.02) !important;
                margin-bottom: 1rem !important;
            }

            /* Styling Tabs trong chế độ tối */
            .stTabs [data-baseweb="tab"] {
                background-color: rgba(255, 255, 255, 0.05) !important;
                color: white !important;
                border-radius: 10px !important;
                margin-right: 5px !important;
            }

            /* Styling Containers trong chế độ tối */
            [data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(255, 255, 255, 0.04) !important;
                border-radius: 20px !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
            }
        
            [data-testid="stExpander"] summary {
                border: none !important;
                padding: 10px 15px !important;
            }

            /* KHỬ VIỀN KHUNG BAO NGOÀI CỦA STREAMLIT (XÓA LỚP CHỮ NHẬT THỪA) */
            div[data-testid="stTextInput"] > div,
            div[data-testid="stTextArea"] > div,
            div[data-testid="stSelectbox"] > div,
            div[data-testid="stNumberInput"] > div,
            div[data-testid="stMultiSelect"] > div {
                border: none !important;
                background-color: transparent !important;
                box-shadow: none !important;
            }

            /* CHỈ ĐỊNH PHONG CÁCH CHO Ô NHẬP LIỆU LÕI (INPUT CORE) */
            div[data-baseweb="input"], 
            div[data-baseweb="select"], 
            div[data-baseweb="textarea"],
            div[data-baseweb="checkbox"],
            div[data-baseweb="base-input"] {
                background-color: #1a1a2e !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 10px !important;
                color: white !important;
            }
        
            /* Đảm bảo chữ gõ vào ô nhập liệu luôn là màu trắng sạch sẽ trong chế độ tối */
            div[data-baseweb="input"] input, 
            div[data-baseweb="base-input"] input,
            div[data-baseweb="textarea"] textarea,
            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input,
            input,
            textarea,
            select {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }

            /* KHỬ HOÀN TOÀN VIỀN/NỀN TRÊN CÁC CHỮ TIÊU ĐỀ (LABELS) */
            [data-testid="stWidgetLabel"], 
            [data-testid="stWidgetLabel"] *,
            div[class*="StyledWidgetLabel"] {
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                margin-bottom: 5px !important;
            }

            /* Nút tăng giảm của ô nhập số */
            .stNumberInput button {
                background-color: #2a5298 !important;
                color: white !important;
                border-radius: 5px !important;
            }

            /* Ép màu DROPDOWN MENU & POPOVER (Sửa lỗi mảng trắng khi chọn) */

            /* Ép màu DROPDOWN MENU & POPOVER (Sửa lỗi mảng trắng khi chọn) */
            div[data-baseweb="popover"], div[role="listbox"], ul[data-baseweb="menu"], 
            div[data-baseweb="popover"] *, [data-baseweb="menu-item"],
            div[data-baseweb="select"] > div, 
            div[data-baseweb="select"] * {
                background-color: #1a1a2e !important;
                color: white !important;
            }
            /* Sửa lỗi chữ trong ô selectbox bị mờ hoặc sai màu */
            div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
                color: white !important;
            }
            div[data-baseweb="select"] svg {
                fill: white !important;
            }
            [data-baseweb="menu-item"]:hover {
                background-color: #2a5298 !important;
            }
        
            /* Loại bỏ các mảng trắng nền của BaseWeb Popover */
            div[data-baseweb="popover"] > div {
                background-color: #1a1a2e !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
            }

            /* Ép màu Expander (Cực kỳ quan trọng cho NCKH tab) */

            /* ĐỊNH NGHĨA KHUÔN HÌNH CHUẨN CHO CÁC THẺ (CARDS) */
            .metric-card {
                background-color: rgba(255, 255, 255, 0.05) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 15px !important;
                padding: 20px !important;
                text-align: center !important;
                margin-bottom: 15px !important;
            }
        
            .stApp[data-test-script-state="running"] .metric-card,
            body.light .metric-card {
                background-color: white !important;
                border: 1px solid #eee !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
            }

            /* === CHẶN OVERLAY MỜ KHI FRAGMENT TỰ REFRESH (run_every) === */
            /* Streamlit thêm opacity: 0.3 vào stale elements khi rerun - ta reset về 1 */
            div[data-stale="true"],
            [data-stale="true"],
            [data-testid="stMainBlockContainer"] [aria-busy="true"],
            .stApp[data-test-script-state="running"] > div,
            .stApp[data-test-script-state="running"] section,
            .stApp[data-test-script-state="running"] [data-testid="stVerticalBlock"],
            .stApp[data-test-script-state="running"] [data-testid="stColumn"],
            .stApp[data-test-script-state="running"] [data-testid="stHorizontalBlock"] {
                opacity: 1 !important;
                filter: none !important;
                transition: none !important;
                pointer-events: auto !important;
                background-color: transparent !important;
            }
            .stApp[data-test-script-state="running"] .stButton button,
            .stApp[data-test-script-state="running"] [data-testid="stBaseButton-primary"],
            .stApp[data-test-script-state="running"] [data-testid="stBaseButton-secondary"] {
                opacity: 1 !important;
            }
            /* Ẩn spinner chạy vòng tròn ở góc trên phải */
            [data-testid="stStatusWidget"] { display: none !important; }

            .metric-value {
                font-size: 1.4rem !important;
                font-weight: 700 !important;
                margin-bottom: 5px !important;
                color: #ffd700 !important;
            }
        
            body.light .metric-value {
                color: #0072ff !important;
            }

            .metric-label {
                font-size: 0.8rem !important;
                color: #aaa !important;
            }
        
            body.light .metric-label {
                color: #666 !important;
            }
            .stExpander, [data-testid="stExpander"], .st-emotion-cache-1839j81 {
                background-color: #16213e !important;
                border: 1px solid rgba(0, 198, 255, 0.2) !important;
                color: white !important;
            }
            .stExpander summary, .stExpander summary * {
                background-color: #1a1a2e !important;
                color: #00c6ff !important;
                font-weight: bold !important;
            }
            .stExpander summary:active,
            .stExpander summary:focus,
            details summary:active,
            details summary:focus {
                background-color: #1a1a2e !important;
                color: #00c6ff !important;
                outline: none !important;
            }
            [data-testid="stAlert"],
            [data-testid="stNotification"] {
                background-color: rgba(22, 33, 62, 0.95) !important;
                color: #e8e8e8 !important;
                border: 1px solid rgba(0, 198, 255, 0.25) !important;
            }
        
            /* Ép màu Sidebar triệt để */
            [data-testid="stSidebar"] {
                background-color: #0d0d1a !important;
                border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
            }
            [data-testid="stSidebar"] * {
                color: white !important;
            }

            /* Fix lỗi chữ mờ (Antialiasing) */
            * {
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                text-rendering: optimizeLegibility;
            }

            /* Fix các khối info-box, metric-card bị trắng */
            .info-box, .metric-card, .member-card, .lecturer-card, .custom-card, .step-box, .stAlert,
            [data-testid="stMetric"], [data-testid="stTable"], [data-testid="stDataFrame"] {
                background-color: rgba(255, 255, 255, 0.05) !important;
                color: white !important;
                border: 1px solid rgba(0, 198, 255, 0.3) !important;
            }

            /* ÉP MÀU CHO BẢNG (TABLE) */
            table, th, td {
                background-color: #1a1a2e !important;
                color: white !important;
                border-color: rgba(255, 255, 255, 0.1) !important;
            }
            thead th {
                background-color: #2a5298 !important;
            }

            /* ÉP MÀU CHO RADIO, CHECKBOX, SLIDER */
            [data-testid="stRadio"] label, [data-testid="stCheckbox"] label, [data-testid="stSlider"] label {
                color: white !important;
            }
            div[role="radiogroup"] div, div[role="checkbox"] {
                color: white !important;
            }
            /* Slider track and thumb */
            div[data-baseweb="slider"] > div {
                background-color: #2a5298 !important;
            }

            /* ÉP MÀU CHO CÁC THÔNG BÁO (SUCCESS, ERROR, INFO) */
            [data-testid="stNotificationContentSuccess"], [data-testid="stNotificationContentError"], 
            [data-testid="stNotificationContentInfo"], [data-testid="stNotificationContentWarning"] {
                background-color: #1a1a2e !important;
                color: white !important;
            }
        
            /* Nút tăng giảm của ô nhập số */
            .stNumberInput button {
                background-color: #2a5298 !important;
                color: white !important;
                border-radius: 5px !important;
            }

            /* Ép màu DROPDOWN MENU & POPOVER (Sửa lỗi mảng trắng khi chọn) */
            ::placeholder {
                color: rgba(255, 255, 255, 0.4) !important;
            }

            /* ÉP MÀU CHO KHU VỰC UPLOAD FILE (QUAN TRỌNG) */
            [data-testid="stFileUploader"] section {
                background-color: #1a1a2e !important;
                border: 1px dashed #00c6ff !important;
                color: white !important;
            }
            [data-testid="stFileUploader"] section div, 
            [data-testid="stFileUploader"] section span,
            [data-testid="stFileUploader"] section small {
                color: #ccc !important;
            }
            /* Nút bấm bên trong uploader */
            [data-testid="stFileUploader"] button {
                background-color: #2a5298 !important;
                color: white !important;
                border: none !important;
            }

            /* ÉP MÀU CHO DANH SÁCH FILE ĐÃ UPLOAD (TỐI ƯU CỰC MẠNH) */
            [data-testid="stFileUploader"] ul, 
            [data-testid="stFileUploader"] ul li,
            [data-testid="stFileUploader"] div[data-testid="stFileUploaderFile"],
            [data-testid="stFileUploader"] div[data-testid="stFileUploaderFile"] > div,
            [data-testid="stFileUploader"] div[data-baseweb="block"],
            [data-testid="stFileUploaderFile"] {
                background-color: #1a1a2e !important;
                color: white !important;
                border: 1px solid #00c6ff !important;
            }
        
            /* ============================================================ */
            /* BẢN KHÔI PHỤC SỰ ỔN ĐỊNH - XÓA BỎ CSS GÂY LỖI TREO THANH CHỌN */
            /* ============================================================ */
        
            /* ============================================================ */
            /* BẢN KHÔI PHỤC BANNER VÀ TAB - CHỈ XÓA VIỀN THỪA CÓ CHỌN LỌC */
            /* ============================================================ */
        
            /* 1. Chỉ xóa viền và nền của các nhãn Widget (Họ tên, Tuổi,...) */
            div[data-testid="stWidgetLabel"], 
            div[data-testid="stWidgetLabel"] *,
            span[data-baseweb="tag"],
            [data-baseweb="tag"] * {
                background-color: transparent !important;
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }

            /* 2. Giữ nguyên màu nền cho các khối Markdown (Banner, Thông báo) */
            /* Không áp dụng lệnh transparent cho stMarkdownContainer chung */

            /* 3. Đảm bảo các ô nhập liệu có khung viền chuẩn */
            div[data-baseweb="input"], 
            div[data-baseweb="select"], 
            div[data-baseweb="textarea"] {
                background-color: #1a1a2e !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 4px !important;
            }

            /* 4. Đảm bảo chữ trắng sạch sẽ cho các vùng văn bản chính */
            .stMarkdown p, .stMarkdown span, label {
                color: white !important;
            }

            /* Sidebar tối giản */
            [data-testid="stSidebarContent"] {
                background-color: #1a1a2e !important;
            }

            /* ĐẢM BẢO VÒNG XOAY LOADING (SPINNER) LUÔN TRẮNG */
            div[data-testid="stLoading"] svg, .stSpinner svg {
                stroke: white !important;
                fill: white !important;
            }

            [data-testid="stFileUploader"] ul li * {
                color: white !important;
            }

            /* ÉP TRẠNG THÁI HOVER ĐỂ KHÔNG BỊ TRẮNG */
            button:hover {
                background-color: #2a5298 !important;
                color: #ffd700 !important;
                border-color: #ffd700 !important;
            }

            /* Popover Button & Container in Dark Mode */
            div[data-testid="stPopover"] button {
                background-color: #1a1a2e !important;
                color: #ffffff !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 10px !important;
            }
            div[data-testid="stPopover"] button * {
                color: #ffffff !important;
            }
            div[data-testid="stPopover"] button:hover {
                background-color: #2a5298 !important;
                border-color: #00c6ff !important;
            }
            div[data-testid="stPopover"] button:hover * {
                color: #ffd700 !important;
            }
            div[data-baseweb="popover"], 
            div[data-baseweb="popover"] div, 
            div[data-baseweb="popover"] ul, 
            div[data-baseweb="popover"] li {
                background-color: #1a1a2e !important;
                color: #ffffff !important;
            }
            div[data-baseweb="popover"] * {
                color: #ffffff !important;
            }

            /* Phong cách st.segmented_control trong chế độ tối giống tab ảnh 2 */
            .st-key-active_tab_widget,
            div[data-testid="stSegmentedControl"],
            div[data-testid="stButtonGroup"] {
                border-bottom: none !important; /* Xóa đường gạch xám nhạt dưới tab bar */
            }
            .st-key-active_tab_widget button,
            div[data-testid="stSegmentedControl"] button,
            div[data-testid="stButtonGroup"] button {
                background-color: rgba(255, 255, 255, 0.05) !important;
                color: rgba(255, 255, 255, 0.8) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-bottom: 2px solid transparent !important;
                padding: 8px 16px !important;
                min-height: 38px !important;
            }
            .st-key-active_tab_widget button:hover,
            div[data-testid="stSegmentedControl"] button:hover,
            div[data-testid="stButtonGroup"] button:hover {
                background-color: rgba(255, 255, 255, 0.1) !important;
                color: #ffffff !important;
                border-color: rgba(255, 255, 255, 0.2) !important;
            }
            .st-key-active_tab_widget button:active,
            .st-key-active_tab_widget button:focus,
            div[data-testid="stSegmentedControl"] button:active,
            div[data-testid="stSegmentedControl"] button:focus,
            div[data-testid="stButtonGroup"] button:active,
            div[data-testid="stButtonGroup"] button:focus {
                background-color: rgba(255, 255, 255, 0.12) !important;
                color: #ffffff !important;
                outline: none !important;
            }
            .st-key-active_tab_widget [aria-pressed="true"],
            .st-key-active_tab_widget [aria-checked="true"],
            .st-key-active_tab_widget [aria-selected="true"],
            .st-key-active_tab_widget [data-checked="true"],
            .st-key-active_tab_widget [class*="selected"],
            .st-key-active_tab_widget [class*="active"],
            .st-key-active_tab_widget button[data-testid*="Active"],
            .st-key-active_tab_widget button[kind*="Active"],
            div[data-testid="stSegmentedControl"] [aria-pressed="true"],
            div[data-testid="stSegmentedControl"] [aria-checked="true"],
            div[data-testid="stSegmentedControl"] [aria-selected="true"],
            div[data-testid="stSegmentedControl"] [data-checked="true"],
            div[data-testid="stSegmentedControl"] button[data-testid*="Active"],
            div[data-testid="stSegmentedControl"] button[kind*="Active"],
            div[data-testid="stButtonGroup"] [aria-pressed="true"],
            div[data-testid="stButtonGroup"] [aria-checked="true"],
            div[data-testid="stButtonGroup"] [aria-selected="true"],
            div[data-testid="stButtonGroup"] [data-checked="true"],
            div[data-testid="stButtonGroup"] button[data-testid*="Active"],
            div[data-testid="stButtonGroup"] button[kind*="Active"] {
                background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important;
                color: #ffffff !important;
                border: 1px solid #00c6ff !important;
                border-bottom: 2px solid #ff4b4b !important; /* Gạch đỏ dưới chân tab được chọn */
            }

            /* ===== SCROLLBAR MÀU TỐI (DARK MODE) ===== */
            .stApp ::-webkit-scrollbar-track,
            [data-testid="stAppViewContainer"] ::-webkit-scrollbar-track,
            [data-testid="stSidebar"] ::-webkit-scrollbar-track,
            .main ::-webkit-scrollbar-track,
            textarea::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.05) !important;
            }
            .stApp ::-webkit-scrollbar-thumb,
            [data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb,
            [data-testid="stSidebar"] ::-webkit-scrollbar-thumb,
            .main ::-webkit-scrollbar-thumb,
            textarea::-webkit-scrollbar-thumb {
                background: linear-gradient(180deg, #00c6ff 0%, #0072ff 100%) !important;
                box-shadow: 0 0 6px rgba(0, 198, 255, 0.4) !important;
            }
            .stApp ::-webkit-scrollbar-thumb:hover,
            [data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb:hover,
            [data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover,
            .main ::-webkit-scrollbar-thumb:hover,
            textarea::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(180deg, #33d1ff 0%, #1a8fff 100%) !important;
                box-shadow: 0 0 10px rgba(0, 198, 255, 0.7) !important;
            }
            /* Firefox scrollbar dark mode */
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .main, textarea {
                scrollbar-width: thin !important;
                scrollbar-color: #0072ff rgba(255,255,255,0.05) !important;
            }
        </style>
        """, unsafe_allow_html=True)
        st.session_state['_last_injected_theme'] = 'dark'

    # === CSS CHO CHẾ ĐỘ SÁNG (LIGHT MODE OVERRIDE) ===
    if st.session_state.get('theme') == 'light' and _current_theme != _last_injected_theme:
        st.markdown("""
        <style>
            .stApp { background: #f8f9fa !important; color: #333 !important; }
            .main-header { background: transparent !important; border: none !important; box-shadow: none !important; }
            .main-header h1 { color: #000000 !important; }
            .main-header p { color: #333333 !important; }
        
            /* Fix container background in Light Mode */
            [data-testid="stVerticalBlockBorderWrapper"] {
                background: #ffffff !important;
                border: 1px solid #ced4da !important; /* Đậm hơn để hiển thị rõ viền */
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            }

            /* Fix Text Input contrast & Caret visibility */
            .stTextInput input, .stTextArea textarea, .stNumberInput input {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 1px solid #ced4da !important;
                caret-color: #0072ff !important; /* Dấu nháy màu xanh chuyên nghiệp, hiển thị rõ trên nền trắng */
            }
        
            /* Hiệu ứng khi nhấn vào ô nhập liệu (Focus) */
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #0072ff !important;
                box-shadow: 0 0 0 2px rgba(0, 114, 255, 0.2) !important;
            }
            .stTextInput label, .stSelectbox label, .stNumberInput label {
                color: #212529 !important;
            }

            .info-box, .metric-card, .member-card, .lecturer-card, .custom-card { 
                background: #ffffff !important; 
                border: 1px solid #e0e0e0 !important; 
                color: #333333 !important;
            }
        
            /* Fix Tabs in Light Mode */
            .stTabs [data-baseweb="tab"] {
                background-color: #f1f3f5 !important;
                color: #495057 !important;
                border-radius: 10px !important;
                margin-right: 5px !important;
            }
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important;
                color: white !important;
            }
        
            /* Fix Vertical Blocks in Light Mode */
            [data-testid="stVerticalBlockBorderWrapper"] {
                background: #ffffff !important;
                border-radius: 20px !important;
                border: 1px solid #ced4da !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            }

            .metric-value { color: #0072ff !important; }
            .metric-label { color: #444444 !important; }
        
            /* Ensure research badge stays white even in light mode */
            .research-badge span { color: #ffffff !important; }
        
            /* Ensure all other text is dark */
            .stMarkdown p, .stMarkdown span, p, span, label, h1, h2, h3, h4, li, div { color: #212529 !important; }
        
            .stTabs [data-baseweb="tab"] { 
                background-color: #f1f3f5 !important; 
                color: #495057 !important; 
                border: 1px solid #ced4da !important;
            }
            .stTabs [aria-selected="true"] { 
                background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important; 
                color: #ffffff !important;
            }
            .footer-container, .footer-col, .footer-bottom { color: #444 !important; }
            .main-footer { background: #f8f9fa !important; border-top: 4px solid #0072ff !important; box-shadow: 0 -5px 15px rgba(0,0,0,0.05) !important; }
            .school-name { color: #1a1a2e !important; }
            .school-subname { color: #0072ff !important; }
            .footer-title { color: #0072ff !important; }
            .stExpander { background: #fff !important; border: 1px solid #ced4da !important; border-radius: 12px !important; }
            .stExpander summary { background: #f8f9fa !important; color: #000 !important; border-bottom: 1px solid #ced4da !important; }
            .stExpander summary:hover { background: #eee !important; }
            [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #ced4da !important; }
            [data-testid="stSidebar"] * { color: #333 !important; }
        
            /* Cải thiện viền cho thanh gạch ngang (Horizontal Rule) */
            hr {
                border: 0 !important;
                border-top: 1px solid #ced4da !important;
                margin: 1rem 0 !important;
                opacity: 1 !important;
            }
        
            /* Làm cho nút gạt (toggle) hiện rõ màu xám khi ở chế độ Sáng */
            div[role="switch"][aria-checked="false"] {
                background-color: #bdc3c7 !important;
            }
            div[role="switch"][aria-checked="false"] > div {
                background-color: #ffffff !important;
            }
            [data-testid="stTable"] th { background-color: #f1f3f5 !important; color: #000 !important; }
            [data-testid="stMetric"] { background: #ffffff !important; border: 1px solid #ced4da !important; padding: 10px !important; border-radius: 12px !important; }
            /* Fix Form elements */
            textarea, input, select { background-color: #ffffff !important; color: #000000 !important; border: 1px solid #adb5bd !important; }
            [data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #adb5bd !important; border-radius: 15px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important; }
        
            /* FIX ALL BUTTONS */
            .stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button,
            .stNumberInput button, [data-testid="stFileUploader"] button { 
                background-color: #f1f3f5 !important; 
                color: #000000 !important; 
                border: 1px solid #ccc !important;
                font-weight: bold !important;
            }
            .stButton button:hover, .stDownloadButton button:hover, [data-testid="stFormSubmitButton"] button:hover,
            .stNumberInput button:hover, [data-testid="stFileUploader"] button:hover { 
                background-color: #e9ecef !important; 
                color: #0072ff !important; 
                border: 1px solid #0072ff !important;
            }
            /* GLOBAL LIGHT MODE OVERRIDES */
            .stApp, [data-testid="stAppViewContainer"] {
                background-color: #ffffff !important;
                color: #000000 !important;
            }

            /* Fix Tabs for Light Mode */
            .stTabs [data-baseweb="tab-list"] {
                background-color: #f8f9fa !important;
                border-radius: 10px 10px 0 0 !important;
            }
            .stTabs [data-baseweb="tab"] {
                color: #495057 !important;
            }
            .stTabs [aria-selected="true"] {
                color: #0072ff !important;
                font-weight: 600 !important;
            }

            /* Fix ALL Selectboxes, MultiSelect, TextInputs, and TextAreas in Light Mode */
            .stSelectbox div[data-baseweb="select"],
            .stSelectbox div[data-baseweb="select"] *,
            .stMultiSelect div[data-baseweb="select"],
            .stMultiSelect div[data-baseweb="select"] *,
            .stTextInput input, 
            .stTextArea textarea,
            .stNumberInput input,
            .stNumberInput div[data-baseweb="input"],
            .stNumberInput div[data-baseweb="input"] *,
            div[data-baseweb="input"] input, 
            div[data-baseweb="base-input"] input,
            div[data-baseweb="textarea"] textarea,
            input,
            textarea,
            select {
                background-color: #ffffff !important;
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                border-color: #ced4da !important;
            }

            /* Fix MultiSelect Tags (selected items) */
            span[data-baseweb="tag"] {
                background-color: #e9ecef !important;
                color: #000000 !important;
                border: 1px solid #0072ff !important;
            }
            span[data-baseweb="tag"] * {
                color: #000000 !important;
            }

            /* Fix Placeholder text color for Light Mode */
            .stTextInput input::placeholder, 
            .stTextArea textarea::placeholder,
            .stNumberInput input::placeholder {
                color: #666666 !important;
                opacity: 0.8 !important;
            }
        
            /* Fix the actual dropdown list and items */
            div[data-baseweb="popover"] div, 
            div[data-baseweb="popover"] ul, 
            div[data-baseweb="popover"] li {
                background-color: #ffffff !important;
                color: #000000 !important;
            }

            /* Fix Sidebar specifically */
            [data-testid="stSidebar"] section[data-testid="stSidebarContent"] {
                background-color: #ffffff !important;
            }

            /* Fix Sidebar Labels and Titles */
            [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
                color: #212529 !important;
                font-weight: 600 !important;
            }

            /* Fix File Uploader */
            [data-testid="stFileUploader"] section {
                background-color: #f8f9fa !important;
                border: 1px dashed #0072ff !important;
                color: #333 !important;
            }
            [data-testid="stFileUploader"] section div { color: #333 !important; }
        
            /* Fix pagination number input buttons */
            .stNumberInput button {
                background-color: #f1f3f5 !important;
                color: #000000 !important;
            }

            /* metric-card Light Mode styling */
            .metric-card {
                background-color: #ffffff !important;
                border: 1px solid #ced4da !important;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
            }
            .metric-label {
                color: #495057 !important;
            }
            .metric-value {
                color: #0072ff !important;
                text-shadow: none !important;
            }

            /* Popover Button in Light Mode */
            div[data-testid="stPopover"] button {
                background-color: #ffffff !important;
                background: #ffffff !important;
                color: #000000 !important;
                border: 1px solid #ced4da !important;
                border-radius: 10px !important;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
            }
            div[data-testid="stPopover"] button * {
                color: #000000 !important;
            }
            div[data-testid="stPopover"] button:hover {
                background-color: #f8f9fa !important;
                background: #f8f9fa !important;
                border-color: #0072ff !important;
            }
            div[data-testid="stPopover"] button:hover * {
                color: #0072ff !important;
            }

            /* Popover Container Content in Light Mode */
            div[data-baseweb="popover"],
            div[data-baseweb="popover"] div,
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] li,
            div[data-baseweb="popover"] span,
            div[data-baseweb="popover"] p,
            div[data-baseweb="popover"] label,
            div[data-baseweb="popover"] button {
                background-color: #ffffff !important;
                background: #ffffff !important;
                color: #000000 !important;
            }
            div[data-baseweb="popover"] * {
                color: #000000 !important;
            }
            div[data-baseweb="popover"] > div {
                background-color: #ffffff !important;
                border: 1px solid #ced4da !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            }

            /* Phong cách st.segmented_control trong chế độ sáng giống tab ảnh 2 */
            .st-key-active_tab_widget,
            div[data-testid="stSegmentedControl"],
            div[data-testid="stButtonGroup"] {
                border-bottom: none !important; /* Xóa đường gạch dưới chân tab bar */
            }
            .st-key-active_tab_widget button,
            div[data-testid="stSegmentedControl"] button,
            div[data-testid="stButtonGroup"] button {
                background-color: #f1f3f5 !important;
                color: #495057 !important;
                border: 1px solid #ced4da !important;
                border-bottom: 2px solid transparent !important;
                padding: 8px 16px !important;
                min-height: 38px !important;
            }
            .st-key-active_tab_widget button:hover,
            div[data-testid="stSegmentedControl"] button:hover,
            div[data-testid="stButtonGroup"] button:hover {
                background-color: #e9ecef !important;
                color: #0072ff !important;
                border-color: #0072ff !important;
            }
            .st-key-active_tab_widget [aria-pressed="true"],
            .st-key-active_tab_widget [aria-checked="true"],
            .st-key-active_tab_widget [aria-selected="true"],
            .st-key-active_tab_widget [data-checked="true"],
            .st-key-active_tab_widget [class*="selected"],
            .st-key-active_tab_widget [class*="active"],
            .st-key-active_tab_widget button[data-testid*="Active"],
            .st-key-active_tab_widget button[kind*="Active"],
            div[data-testid="stSegmentedControl"] [aria-pressed="true"],
            div[data-testid="stSegmentedControl"] [aria-checked="true"],
            div[data-testid="stSegmentedControl"] [aria-selected="true"],
            div[data-testid="stSegmentedControl"] [data-checked="true"],
            div[data-testid="stSegmentedControl"] button[data-testid*="Active"],
            div[data-testid="stSegmentedControl"] button[kind*="Active"],
            div[data-testid="stButtonGroup"] [aria-pressed="true"],
            div[data-testid="stButtonGroup"] [aria-checked="true"],
            div[data-testid="stButtonGroup"] [aria-selected="true"],
            div[data-testid="stButtonGroup"] [data-checked="true"],
            div[data-testid="stButtonGroup"] button[data-testid*="Active"],
            div[data-testid="stButtonGroup"] button[kind*="Active"] {
                background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important;
                color: #ffffff !important;
                border: 1px solid #00c6ff !important;
                border-bottom: 2px solid #ff4b4b !important; /* Gạch đỏ dưới chân tab được chọn */
            }

            /* ===== SCROLLBAR MÀU SÁNG (LIGHT MODE) ===== */
            .stApp ::-webkit-scrollbar-track,
            [data-testid="stAppViewContainer"] ::-webkit-scrollbar-track,
            [data-testid="stSidebar"] ::-webkit-scrollbar-track,
            .main ::-webkit-scrollbar-track,
            textarea::-webkit-scrollbar-track {
                background: rgba(0, 0, 0, 0.06) !important;
                border-radius: 10px !important;
            }
            .stApp ::-webkit-scrollbar-thumb,
            [data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb,
            [data-testid="stSidebar"] ::-webkit-scrollbar-thumb,
            .main ::-webkit-scrollbar-thumb,
            textarea::-webkit-scrollbar-thumb {
                background: linear-gradient(180deg, #90caf9 0%, #1565c0 100%) !important;
                border-radius: 10px !important;
            }
            .stApp ::-webkit-scrollbar-thumb:hover,
            [data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb:hover,
            [data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover,
            .main ::-webkit-scrollbar-thumb:hover,
            textarea::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(180deg, #42a5f5 0%, #0d47a1 100%) !important;
                box-shadow: 0 0 8px rgba(21, 101, 192, 0.5) !important;
            }
            /* Firefox scrollbar light mode */
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .main, textarea {
                scrollbar-width: thin !important;
                scrollbar-color: #1565c0 rgba(0,0,0,0.06) !important;
            }
        </style>
        """, unsafe_allow_html=True)
        st.session_state['_last_injected_theme'] = 'light'

    if inject_design_system:
        inject_design_system(is_light=(st.session_state.get('theme') == 'light'))
    if inject_auth_nav_css:
        inject_auth_nav_css()
    if inject_streamlit_skin:
        inject_streamlit_skin(is_light=(st.session_state.get('theme') == 'light'))
    if inject_ncv_dashboard_css:
        inject_ncv_dashboard_css()
