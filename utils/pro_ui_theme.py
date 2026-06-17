"""Final presentation layer for the Streamlit UI.

This module intentionally only injects CSS. It does not change widgets,
session state, callbacks, tabs, subtabs, or any application logic.
"""

import streamlit as st


PRO_UI_FONT_IMPORT = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700;800&"
    "family=Fraunces:opsz,wght@9..144,500;9..144,600&"
    "family=IBM+Plex+Mono:wght@400;500;600&display=swap"
)


def inject_pro_ui_theme() -> None:
    """Inject a polished clinical UI skin inspired by the HTML demo."""
    st.markdown(
        f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{PRO_UI_FONT_IMPORT}">
<style id="rehab-pro-ui-theme">
:root {{
  --rehab-ui: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --rehab-display: 'Fraunces', Georgia, 'Times New Roman', serif;
  --rehab-mono: 'IBM Plex Mono', ui-monospace, 'Cascadia Code', monospace;
  --rehab-bg: #e8edf5;
  --rehab-bg-mesh-1: rgba(31, 111, 224, .10);
  --rehab-bg-mesh-2: rgba(90, 99, 216, .08);
  --rehab-surface: #ffffff;
  --rehab-surface-2: #f4f7fc;
  --rehab-surface-3: #edf2fa;
  --rehab-glass: rgba(255, 255, 255, .74);
  --rehab-ink: #0f1a26;
  --rehab-ink-2: #39506a;
  --rehab-ink-3: #6c7e92;
  --rehab-blue: #1f6fe0;
  --rehab-blue-strong: #1657bc;
  --rehab-blue-soft: rgba(31, 111, 224, .12);
  --rehab-ai: #5a63d8;
  --rehab-ai-soft: rgba(90, 99, 216, .12);
  --rehab-ok: #16a34a;
  --rehab-warn: #c9820e;
  --rehab-danger: #d2453a;
  --rehab-line: #dfe6f1;
  --rehab-line-2: #edf1f9;
  --rehab-shadow-sm: 0 1px 2px rgba(15, 28, 24, .06), 0 1px 3px rgba(15, 28, 24, .05);
  --rehab-shadow: 0 4px 14px rgba(15, 28, 24, .07), 0 2px 5px rgba(15, 28, 24, .05);
  --rehab-shadow-lg: 0 24px 60px rgba(15, 28, 24, .16), 0 8px 24px rgba(15, 28, 24, .10);
  --rehab-radius-sm: 8px;
  --rehab-radius: 12px;
  --rehab-radius-lg: 18px;
  --rehab-radius-xl: 24px;
}}

html,
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMarkdownContainer"],
button,
input,
textarea,
select {{
  font-family: var(--rehab-ui) !important;
  letter-spacing: 0 !important;
}}

html {{
  overflow-y: scroll !important;
  background: var(--rehab-bg) !important;
}}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMainViewContainer"] {{
  color: var(--rehab-ink) !important;
  background-color: var(--rehab-bg) !important;
  background-image:
    radial-gradient(60vw 50vh at 8% -8%, var(--rehab-bg-mesh-1), transparent 60%),
    radial-gradient(55vw 50vh at 105% 0%, var(--rehab-bg-mesh-2), transparent 55%) !important;
  background-attachment: fixed !important;
  -webkit-font-smoothing: antialiased !important;
  text-rendering: optimizeLegibility !important;
}}

[data-testid="stHeader"] {{
  background: var(--rehab-glass) !important;
  border-bottom: 1px solid var(--rehab-line) !important;
  backdrop-filter: saturate(160%) blur(14px) !important;
  -webkit-backdrop-filter: saturate(160%) blur(14px) !important;
  box-shadow: none !important;
}}

[data-testid="stToolbar"] {{
  color: var(--rehab-ink-2) !important;
}}

[data-testid="stAppViewBlockContainer"],
.main .block-container,
.block-container {{
  max-width: 1180px !important;
  padding-top: 1.25rem !important;
  padding-left: clamp(1rem, 2.5vw, 2rem) !important;
  padding-right: clamp(1rem, 2.5vw, 2rem) !important;
  padding-bottom: 8rem !important;
}}

section[data-testid="stSidebar"] {{
  background: rgba(255, 255, 255, .68) !important;
  border-right: 1px solid var(--rehab-line) !important;
  backdrop-filter: saturate(155%) blur(14px) !important;
  -webkit-backdrop-filter: saturate(155%) blur(14px) !important;
}}

section[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] {{
  background: transparent !important;
}}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
  color: var(--rehab-ink) !important;
  font-family: var(--rehab-display) !important;
  font-weight: 600 !important;
  letter-spacing: 0 !important;
}}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] div {{
  color: var(--rehab-ink-2) !important;
}}

.main-header {{
  position: relative !important;
  background: var(--rehab-surface) !important;
  border: 1px solid var(--rehab-line) !important;
  box-shadow: var(--rehab-shadow-sm) !important;
  border-radius: var(--rehab-radius-lg) !important;
  padding: clamp(1rem, 2.2vw, 1.6rem) !important;
  text-align: center !important;
  overflow: hidden !important;
}}

.main-header::before {{
  content: "" !important;
  position: absolute !important;
  inset: 0 0 auto 0 !important;
  height: 4px !important;
  background: linear-gradient(90deg, var(--rehab-blue), var(--rehab-ai)) !important;
}}

.main-header .header-logos-row {{
  gap: 14px !important;
  margin: 0 auto .65rem auto !important;
  padding: 0 !important;
  max-width: 460px !important;
}}

.main-header .header-logo-glow {{
  width: 52px !important;
  height: 52px !important;
  border-radius: 14px !important;
  border: 1px solid var(--rehab-line) !important;
  background: var(--rehab-surface-2) !important;
  box-shadow: var(--rehab-shadow-sm) !important;
  animation: none !important;
  padding: 4px !important;
}}

.main-header .header-logo-glow img {{
  width: 42px !important;
  height: 42px !important;
  border-radius: 11px !important;
  object-fit: contain !important;
}}

.main-header h1,
.main-header h1 *,
h1.app-title,
h1.app-title * {{
  color: var(--rehab-ink) !important;
  font-family: var(--rehab-display) !important;
  font-size: clamp(1.65rem, 3.2vw, 2.45rem) !important;
  line-height: 1.08 !important;
  font-weight: 600 !important;
  text-transform: none !important;
  text-shadow: none !important;
  letter-spacing: 0 !important;
  margin: 0 !important;
}}

.main-header h1 + div {{
  width: 96px !important;
  height: 3px !important;
  background: linear-gradient(90deg, var(--rehab-blue), var(--rehab-ai)) !important;
  margin: .7rem auto .75rem auto !important;
  border-radius: 999px !important;
}}

.main-header p,
.main-header p * {{
  color: var(--rehab-ink-2) !important;
  font-family: var(--rehab-ui) !important;
  font-size: clamp(.95rem, 1.5vw, 1.08rem) !important;
  font-style: normal !important;
  opacity: 1 !important;
}}

.research-badge {{
  background: transparent !important;
  padding: 0 !important;
}}

.research-badge span {{
  display: inline-flex !important;
  align-items: center !important;
  gap: .4rem !important;
  background: var(--rehab-blue-soft) !important;
  color: var(--rehab-blue-strong) !important;
  border: 1px solid rgba(31, 111, 224, .16) !important;
  border-radius: 999px !important;
  padding: .35rem .85rem !important;
  font-family: var(--rehab-ui) !important;
  font-size: .78rem !important;
  font-weight: 700 !important;
}}

h1, h2, h3, h4 {{
  color: var(--rehab-ink) !important;
  letter-spacing: 0 !important;
}}

.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3,
.stMarkdown h4 {{
  font-family: var(--rehab-display) !important;
  font-weight: 600 !important;
  line-height: 1.15 !important;
}}

.stMarkdown p,
.stMarkdown li,
.stMarkdown span,
p, li, label {{
  color: var(--rehab-ink-2) !important;
  font-size: .98rem !important;
  line-height: 1.58 !important;
}}

[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stExpander"],
.info-box,
.custom-card,
.metric-card,
.member-card,
.lecturer-card,
.research-table-container,
[data-testid="stMetric"],
[data-testid="stAlert"],
[data-testid="stNotification"] {{
  background: var(--rehab-surface) !important;
  color: var(--rehab-ink) !important;
  border: 1px solid var(--rehab-line) !important;
  border-radius: var(--rehab-radius) !important;
  box-shadow: var(--rehab-shadow-sm) !important;
}}

[data-testid="stVerticalBlockBorderWrapper"] {{
  overflow: hidden !important;
}}

.metric-card {{
  padding: 1rem !important;
  text-align: center !important;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease !important;
}}

.metric-card:hover {{
  transform: translateY(-2px) !important;
  border-color: rgba(31, 111, 224, .28) !important;
  box-shadow: var(--rehab-shadow) !important;
}}

.metric-value {{
  color: var(--rehab-blue-strong) !important;
  font-family: var(--rehab-mono) !important;
  font-size: clamp(1.35rem, 2.6vw, 1.8rem) !important;
  font-weight: 600 !important;
  letter-spacing: 0 !important;
}}

.metric-label,
.member-role {{
  color: var(--rehab-ink-3) !important;
  font-size: .82rem !important;
  font-weight: 600 !important;
}}

.member-name,
.lecturer-name {{
  color: var(--rehab-ink) !important;
  font-weight: 700 !important;
}}

.info-box,
.warning-box {{
  border-left: 3px solid var(--rehab-blue) !important;
  padding: 1rem 1.1rem !important;
}}

.warning-box {{
  border-color: var(--rehab-warn) !important;
  background: rgba(201, 130, 14, .12) !important;
}}

.stButton > button,
.stDownloadButton > button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"] {{
  min-height: 2.65rem !important;
  border-radius: var(--rehab-radius) !important;
  border: 1px solid var(--rehab-line) !important;
  background: var(--rehab-surface) !important;
  color: var(--rehab-ink-2) !important;
  box-shadow: var(--rehab-shadow-sm) !important;
  font-family: var(--rehab-ui) !important;
  font-size: .92rem !important;
  font-weight: 700 !important;
  letter-spacing: 0 !important;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease, background .16s ease, color .16s ease !important;
}}

.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"],
[data-testid="stBaseButton-primary"] {{
  border-color: transparent !important;
  background: linear-gradient(145deg, var(--rehab-blue), var(--rehab-blue-strong)) !important;
  color: #ffffff !important;
  box-shadow: 0 8px 20px rgba(31, 111, 224, .18) !important;
}}

.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-secondary"]:hover {{
  transform: translateY(-1px) !important;
  border-color: var(--rehab-blue) !important;
  color: var(--rehab-blue-strong) !important;
  box-shadow: var(--rehab-shadow) !important;
}}

.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {{
  color: #ffffff !important;
  background: linear-gradient(145deg, var(--rehab-blue-strong), var(--rehab-blue)) !important;
  box-shadow: 0 12px 26px rgba(31, 111, 224, .22) !important;
}}

.stButton > button p,
.stDownloadButton > button p,
[data-testid="stFormSubmitButton"] button p,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-secondary"] p {{
  color: inherit !important;
  font-size: inherit !important;
  font-weight: inherit !important;
}}

.stTabs [data-baseweb="tab-list"],
[data-testid="stSegmentedControl"] [role="radiogroup"],
[data-testid="stButtonGroup"] [role="radiogroup"],
.st-key-active_tab_widget [role="radiogroup"] {{
  gap: .5rem !important;
  padding: .25rem !important;
  background: var(--rehab-surface-2) !important;
  border: 1px solid var(--rehab-line) !important;
  border-radius: var(--rehab-radius) !important;
  overflow-x: auto !important;
  overflow-y: hidden !important;
  box-shadow: none !important;
}}

.stTabs [data-baseweb="tab"],
[data-testid="stSegmentedControl"] button,
[data-testid="stButtonGroup"] button,
.st-key-active_tab_widget button {{
  min-height: 2.35rem !important;
  border-radius: 9px !important;
  border: 1px solid transparent !important;
  background: transparent !important;
  color: var(--rehab-ink-3) !important;
  padding: .45rem .85rem !important;
  white-space: nowrap !important;
  box-shadow: none !important;
  flex-shrink: 0 !important;
}}

.stTabs [data-baseweb="tab"] p,
[data-testid="stSegmentedControl"] button p,
[data-testid="stButtonGroup"] button p,
.st-key-active_tab_widget button p,
.stTabs [data-baseweb="tab"] div {{
  color: inherit !important;
  font-size: .86rem !important;
  font-weight: 700 !important;
  text-transform: none !important;
  line-height: 1.2 !important;
}}

.stTabs [aria-selected="true"],
[data-testid="stSegmentedControl"] [aria-checked="true"],
[data-testid="stSegmentedControl"] [aria-pressed="true"],
[data-testid="stButtonGroup"] [aria-checked="true"],
[data-testid="stButtonGroup"] [aria-pressed="true"],
.st-key-active_tab_widget [aria-checked="true"],
.st-key-active_tab_widget [aria-pressed="true"] {{
  background: var(--rehab-surface) !important;
  color: var(--rehab-blue-strong) !important;
  border-color: var(--rehab-line) !important;
  box-shadow: var(--rehab-shadow-sm) !important;
}}

div[data-baseweb="input"],
div[data-baseweb="select"],
div[data-baseweb="textarea"],
div[data-baseweb="base-input"],
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {{
  background: var(--rehab-surface-2) !important;
  border: 1px solid var(--rehab-line) !important;
  border-radius: var(--rehab-radius) !important;
  color: var(--rehab-ink) !important;
  box-shadow: none !important;
}}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
textarea,
input {{
  color: var(--rehab-ink) !important;
  -webkit-text-fill-color: var(--rehab-ink) !important;
  caret-color: var(--rehab-blue) !important;
}}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="select"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="base-input"]:focus-within {{
  background: var(--rehab-surface) !important;
  border-color: var(--rehab-blue) !important;
  box-shadow: 0 0 0 3px var(--rehab-blue-soft) !important;
}}

[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] * {{
  color: var(--rehab-ink-2) !important;
  font-weight: 700 !important;
}}

[data-testid="stFileUploader"] section {{
  background: var(--rehab-surface-2) !important;
  border: 1px dashed rgba(31, 111, 224, .35) !important;
  border-radius: var(--rehab-radius-lg) !important;
  color: var(--rehab-ink-2) !important;
}}

[data-testid="stFileUploader"] section * {{
  color: var(--rehab-ink-2) !important;
}}

[data-testid="stExpander"] summary {{
  background: var(--rehab-surface-2) !important;
  color: var(--rehab-ink) !important;
  border-radius: var(--rehab-radius) !important;
  font-weight: 700 !important;
}}

table,
[data-testid="stTable"],
[data-testid="stDataFrame"] {{
  background: var(--rehab-surface) !important;
  color: var(--rehab-ink) !important;
  border-color: var(--rehab-line) !important;
}}

thead th {{
  background: var(--rehab-surface-2) !important;
  color: var(--rehab-ink-3) !important;
  font-size: .78rem !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
}}

td, th {{
  border-color: var(--rehab-line-2) !important;
}}

div[data-baseweb="popover"],
div[role="listbox"],
ul[data-baseweb="menu"],
[data-baseweb="menu-item"] {{
  background: var(--rehab-surface) !important;
  color: var(--rehab-ink) !important;
  border-color: var(--rehab-line) !important;
}}

[data-baseweb="menu-item"]:hover {{
  background: var(--rehab-surface-2) !important;
}}

[data-testid="stMetric"] [data-testid="stMetricValue"],
[data-testid="stMetric"] [data-testid="stMetricValue"] * {{
  color: var(--rehab-blue-strong) !important;
  font-family: var(--rehab-mono) !important;
  font-weight: 600 !important;
}}

[data-testid="stAlert"] *,
[data-testid="stNotification"] * {{
  color: var(--rehab-ink-2) !important;
}}

video,
div[data-testid="stImage"] img,
.frame-thumbnail {{
  border-radius: var(--rehab-radius) !important;
  box-shadow: var(--rehab-shadow) !important;
}}

::-webkit-scrollbar {{
  width: 8px !important;
  height: 8px !important;
}}

::-webkit-scrollbar-track {{
  background: rgba(15, 26, 38, .05) !important;
  border-radius: 999px !important;
}}

::-webkit-scrollbar-thumb {{
  background: linear-gradient(180deg, var(--rehab-blue), var(--rehab-blue-strong)) !important;
  border: 2px solid transparent !important;
  background-clip: padding-box !important;
  border-radius: 999px !important;
}}

@media (max-width: 768px) {{
  [data-testid="stAppViewBlockContainer"],
  .main .block-container,
  .block-container {{
    padding-left: .85rem !important;
    padding-right: .85rem !important;
  }}

  .main-header {{
    padding: .95rem !important;
  }}

  .main-header .header-logo-glow {{
    width: 44px !important;
    height: 44px !important;
  }}

  .main-header .header-logo-glow img {{
    width: 35px !important;
    height: 35px !important;
  }}
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --rehab-bg: #0a1119;
    --rehab-bg-mesh-1: rgba(91, 155, 255, .13);
    --rehab-bg-mesh-2: rgba(139, 147, 248, .10);
    --rehab-surface: #101a27;
    --rehab-surface-2: #152130;
    --rehab-surface-3: #1a2839;
    --rehab-glass: rgba(16, 26, 39, .66);
    --rehab-ink: #e8eef7;
    --rehab-ink-2: #a9bccf;
    --rehab-ink-3: #7c8b9b;
    --rehab-blue: #5b9bff;
    --rehab-blue-strong: #8bb6ff;
    --rehab-blue-soft: rgba(91, 155, 255, .16);
    --rehab-ai: #8b93f8;
    --rehab-ai-soft: rgba(139, 147, 248, .16);
    --rehab-line: #1f2c3b;
    --rehab-line-2: #18222f;
    --rehab-shadow-sm: 0 1px 2px rgba(0, 0, 0, .35);
    --rehab-shadow: 0 6px 22px rgba(0, 0, 0, .38);
    --rehab-shadow-lg: 0 28px 70px rgba(0, 0, 0, .55);
  }}

  .stButton > button[kind="primary"],
  [data-testid="stBaseButton-primary"] {{
    color: #06182e !important;
  }}
}}
</style>
""",
        unsafe_allow_html=True,
    )
