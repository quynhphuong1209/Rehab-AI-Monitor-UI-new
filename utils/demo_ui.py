# -*- coding: utf-8 -*-
"""
demo_ui.py — Thư viện UI "clinical-teal" port nguyên từ rehab_ai_monitor_demo.html.

Mục tiêu: dựng lại giao diện Streamlit cho TẤT CẢ vai trò (BN/BS/KTV/NCV/QTV) +
màn đăng nhập GIỐNG Y bản HTML demo. Tất cả component (card, stat, ring, chart,
bảng, pill, note, VAS...) được tái hiện bằng HTML/SVG + CSS giống hệt demo.

Cách dùng trong app.py:
    from demo_ui import inject_design_system, page_head, stat, ring, ...
    inject_design_system(is_light=True)   # gọi mỗi rerun, sớm
    st.markdown(page_head("Tiêu đề","Phụ đề", actions_html), unsafe_allow_html=True)
    st.markdown(stat("i-users","Đang điều trị","18","+2","up","tuần này"), unsafe_allow_html=True)
"""
import math
import streamlit as st

# ============================================================ ICON SPRITE
# Bộ icon line (stroke) port nguyên từ demo — dùng qua <svg class="icon"><use href="#i-..."/></svg>
_ICON_SPRITE = """
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
<symbol id="i-pulse" viewBox="0 0 24 24"><path d="M3 12h3l2.5-7 4 14 2.5-9 1.5 2H21"/></symbol>
<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M4.2 4.2l1.8 1.8M18 18l1.8 1.8M2 12h2.5M19.5 12H22M4.2 19.8 6 18M18 6l1.8-1.8"/></symbol>
<symbol id="i-moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z"/></symbol>
<symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M5 21c0-3.9 3.1-7 7-7s7 3.1 7 7"/></symbol>
<symbol id="i-lock" viewBox="0 0 24 24"><rect x="4.5" y="11" width="15" height="9" rx="2.2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></symbol>
<symbol id="i-mail" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2.2"/><path d="m3.5 6.5 8.5 6 8.5-6"/></symbol>
<symbol id="i-stetho" viewBox="0 0 24 24"><path d="M6 3v5a4 4 0 0 0 8 0V3M5 3h2M13 3h2M10 16v1a4 4 0 0 0 8 0v-2"/><circle cx="18" cy="11" r="2.2"/></symbol>
<symbol id="i-tools" viewBox="0 0 24 24"><path d="M14.5 5.5a3.5 3.5 0 0 0-4.6 4.4L3 16.7 5.3 19l6.8-6.9a3.5 3.5 0 0 0 4.4-4.6l-2.2 2.2-2-2 2.2-2.2Z"/></symbol>
<symbol id="i-micro" viewBox="0 0 24 24"><path d="M6 18h12M9 18V9l3-1.5M9 13l4-2"/><circle cx="14.5" cy="6.5" r="2.5"/><path d="M13 16a5 5 0 0 0 5-5"/></symbol>
<symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 3 5 6v5c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6Z"/></symbol>
<symbol id="i-shield-c" viewBox="0 0 24 24"><path d="M12 3 5 6v5c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6Z"/><path d="m9 11.5 2 2 4-4"/></symbol>
<symbol id="i-heart" viewBox="0 0 24 24"><path d="M12 20s-7-4.6-9.2-9C1.3 8 3 4.5 6.4 4.5c2 0 3.2 1.2 3.6 2 .4-.8 1.6-2 3.6-2 3.4 0 5.1 3.5 3.6 6.5C19 15.4 12 20 12 20Z"/></symbol>
<symbol id="i-dumbbell" viewBox="0 0 24 24"><path d="M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10"/></symbol>
<symbol id="i-check" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m8.5 12 2.5 2.5L16 9.5"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/></symbol>
<symbol id="i-spark" viewBox="0 0 24 24"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/></symbol>
<symbol id="i-chart" viewBox="0 0 24 24"><path d="M4 4v16h16"/><path d="M8 14l3-3 3 2 4-5"/></symbol>
<symbol id="i-bars" viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-7M22 20h-20"/></symbol>
<symbol id="i-cal" viewBox="0 0 24 24"><rect x="3.5" y="5" width="17" height="16" rx="2.2"/><path d="M3.5 9.5h17M8 3v3M16 3v3"/></symbol>
<symbol id="i-bell" viewBox="0 0 24 24"><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 20a2 2 0 0 0 4 0"/></symbol>
<symbol id="i-video" viewBox="0 0 24 24"><rect x="3" y="6" width="13" height="12" rx="2.2"/><path d="m16 10 5-3v10l-5-3z"/></symbol>
<symbol id="i-vas" viewBox="0 0 24 24"><path d="M3 12h18M3 12c2-4 4-6 9-6s7 2 9 6c-2 4-4 6-9 6s-7-2-9-6Z"/></symbol>
<symbol id="i-users" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><path d="M16 4.5a3.2 3.2 0 0 1 0 6.4M21 20c0-2.6-1.6-4.8-4-5.6"/></symbol>
<symbol id="i-db" viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="7.5" ry="3"/><path d="M4.5 6v12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6M4.5 12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3"/></symbol>
<symbol id="i-cog" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M21.5 12h-3M5.5 12h-3M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1M18.4 18.4l-2.1-2.1M7.7 7.7 5.6 5.6"/></symbol>
<symbol id="i-log" viewBox="0 0 24 24"><path d="M5 4h11l3 3v13H5zM9 4v4h7"/><path d="M8 13h8M8 16.5h5"/></symbol>
<symbol id="i-broom" viewBox="0 0 24 24"><path d="M14 4 9.5 8.5M19 9l-9.5 9.5L5 20l1-4.5L15.5 6M9 14l1 1"/></symbol>
<symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14m0 0-6-6m6 6-6 6"/></symbol>
<symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></symbol>
<symbol id="i-logout" viewBox="0 0 24 24"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 16l4-4-4-4M14 12H3"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></symbol>
<symbol id="i-bone" viewBox="0 0 24 24"><path d="M7 7a2.5 2.5 0 1 0-2 4l6 6a2.5 2.5 0 1 0 4 2 2.5 2.5 0 1 0 2-4l-6-6a2.5 2.5 0 1 0-4-2Z"/></symbol>
<symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/></symbol>
<symbol id="i-flask" viewBox="0 0 24 24"><path d="M9 3h6M10 3v6L5 18a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 18l-5-9V3"/><path d="M7.5 14h9"/></symbol>
<symbol id="i-doc" viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6zM14 3v4h4"/><path d="M9 12h6M9 15.5h6M9 8.5h3"/></symbol>
</svg>
"""

_ICON_FIX = {"i-scale2": "i-target"}
def _ic(i): return _ICON_FIX.get(i, i)

# ============================================================ TOKENS (light/dark)
_TOKENS_LIGHT = (
    ":root{--ui:'Inter','Be Vietnam Pro',system-ui,sans-serif;--display:'Fraunces',Georgia,serif;"
    "--mono:'IBM Plex Mono',ui-monospace,monospace;--bg:#e8edf5;--bg-mesh-1:rgba(31,111,224,.10);--bg-mesh-2:rgba(99,102,241,.07);"
    "--surface:#ffffff;--surface-2:#f4f7fc;--surface-3:#edf2fa;--glass:rgba(255,255,255,.72);"
    "--ink:#0f1a26;--ink-2:#39506a;--ink-3:#6c7e92;--teal:#1f6fe0;--teal-strong:#1657bc;"
    "--teal-50:rgba(31,111,224,.12);--teal-12:rgba(31,111,224,.10);--ai:#5a63d8;--ai-50:rgba(90,99,216,.12);"
    "--danger:#d2453a;--danger-50:rgba(210,69,58,.12);--warn:#c9820e;--warn-50:rgba(201,130,14,.14);--ok:#16a34a;"
    "--line:#dfe6f1;--line-2:#edf1f9;--shadow-sm:0 1px 2px rgba(15,28,24,.06),0 1px 3px rgba(15,28,24,.05);"
    "--shadow:0 4px 14px rgba(15,28,24,.07),0 2px 5px rgba(15,28,24,.05);--shadow-lg:0 24px 60px rgba(15,28,24,.16),0 8px 24px rgba(15,28,24,.10);"
    "--r-xs:8px;--r-sm:11px;--r:15px;--r-lg:22px;--r-xl:28px;}"
)
_TOKENS_DARK = (
    ":root{--ui:'Inter','Be Vietnam Pro',system-ui,sans-serif;--display:'Fraunces',Georgia,serif;"
    "--mono:'IBM Plex Mono',ui-monospace,monospace;--bg:#0a1119;--bg-mesh-1:rgba(91,155,255,.13);--bg-mesh-2:rgba(99,102,241,.10);"
    "--surface:#101a27;--surface-2:#152130;--surface-3:#1a2839;--glass:rgba(16,26,39,.66);"
    "--ink:#e8eef7;--ink-2:#a9bccf;--ink-3:#7c8b9b;--teal:#5b9bff;--teal-strong:#8bb6ff;"
    "--teal-50:rgba(91,155,255,.16);--teal-12:rgba(91,155,255,.10);--ai:#8b93f8;--ai-50:rgba(139,147,248,.16);"
    "--danger:#f0786c;--danger-50:rgba(240,120,108,.16);--warn:#e7b15a;--warn-50:rgba(231,177,90,.16);--ok:#34d399;"
    "--line:#1f2c3b;--line-2:#18222f;--shadow-sm:0 1px 2px rgba(0,0,0,.4);--shadow:0 6px 22px rgba(0,0,0,.45);"
    "--shadow-lg:0 28px 70px rgba(0,0,0,.6);--r-xs:8px;--r-sm:11px;--r:15px;--r-lg:22px;--r-xl:28px;}"
)

# ============================================================ COMPONENT CSS (port nguyên demo)
_COMPONENT_CSS = """
.duk *{box-sizing:border-box}
.duk .mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
.duk .muted{color:var(--ink-3)}
.duk .icon{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;flex:none;vertical-align:middle}
.duk .icon.sm{width:15px;height:15px}
.duk .icon.lg{width:26px;height:26px}
/* page head */
.duk .page-head{display:flex;align-items:flex-end;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:20px}
.duk .page-head h1{font-family:var(--display);font-weight:600;font-size:clamp(22px,3vw,30px);margin:0;letter-spacing:-.3px;color:var(--ink)}
.duk .page-head .sub{font-size:13.5px;color:var(--ink-3);margin-top:3px}
.duk .page-head .actions{display:flex;gap:9px;flex-wrap:wrap}
/* grid */
.duk .grid{display:grid;gap:16px}
.duk .g-3{grid-template-columns:repeat(3,1fr)}
.duk .g-2{grid-template-columns:repeat(2,1fr)}
.duk .g-21{grid-template-columns:1.4fr 1fr}
.duk .g-12{grid-template-columns:1fr 1.6fr}
/* card */
.duk .card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow-sm);overflow:hidden}
.duk .card.pad{padding:18px}
.duk .card-h{display:flex;align-items:center;gap:9px;padding:15px 18px;border-bottom:1px solid var(--line-2)}
.duk .card-h .icon{width:17px;height:17px;color:var(--teal)}
.duk .card-h h3{font-size:14.5px;font-weight:600;margin:0;flex:1;color:var(--ink)}
.duk .card-h .tag{font-size:11px;color:var(--ink-3);font-weight:600}
.duk .card-b{padding:18px;color:var(--ink-2)}
.duk .section-label{display:flex;align-items:center;gap:8px;font-size:11.5px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--ink-3);margin-bottom:13px}
.duk .section-label .icon{width:15px;height:15px;color:var(--teal)}
/* stat */
.duk .stat{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px;box-shadow:var(--shadow-sm)}
.duk .stat .top{display:flex;align-items:center;justify-content:space-between;margin-bottom:9px}
.duk .stat .top .ico{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:var(--teal-12);color:var(--teal-strong)}
.duk .stat .top .ico .icon{width:18px;height:18px}
.duk .stat .top .trend{font-size:11.5px;font-weight:600;font-family:var(--mono)}
.duk .stat .trend.up{color:var(--ok)} .duk .stat .trend.down{color:var(--danger)}
.duk .stat .v{font-family:var(--mono);font-size:27px;font-weight:600;letter-spacing:-.5px;color:var(--ink)}
.duk .stat .l{font-size:12.5px;color:var(--ink-3);margin-top:2px}
/* pill */
.duk .pill{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;font-size:11.5px;font-weight:600}
.duk .pill .icon{width:12px;height:12px}
.duk .pill.ok{background:var(--teal-50);color:var(--teal-strong)}
.duk .pill.bad{background:var(--danger-50);color:var(--danger)}
.duk .pill.warn{background:var(--warn-50);color:var(--warn)}
.duk .pill.ai{background:var(--ai-50);color:var(--ai)}
.duk .pill.neu{background:var(--surface-3);color:var(--ink-2)}
/* meter */
.duk .meter{height:8px;border-radius:99px;background:var(--surface-3);overflow:hidden;margin:7px 0}
.duk .meter i{display:block;height:100%;border-radius:99px;background:var(--teal)}
.duk .meter.bad i{background:var(--danger)} .duk .meter.warn i{background:var(--warn)} .duk .meter.ai i{background:var(--ai)}
/* tables */
.duk .tbl{width:100%;border-collapse:collapse;font-size:13px}
.duk .tbl th{text-align:left;font-size:11px;font-weight:700;letter-spacing:.3px;text-transform:uppercase;color:var(--ink-3);padding:10px 14px;border-bottom:1px solid var(--line)}
.duk .tbl td{padding:12px 14px;border-bottom:1px solid var(--line-2);color:var(--ink-2)}
.duk .tbl tr:last-child td{border-bottom:none}
.duk .tbl tr.hl:hover td{background:var(--surface-2)}
.duk .tbl .who{display:flex;align-items:center;gap:10px}
.duk .tbl .who .av{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font-size:11px;font-weight:700;color:#fff;background:var(--ink-3)}
.duk .tbl .who b{color:var(--ink);font-weight:600}
.duk .tbl .who span{font-size:11px;color:var(--ink-3)}
/* lists */
.duk .listrow{display:flex;align-items:center;gap:13px;padding:13px 0;border-bottom:1px solid var(--line-2)}
.duk .listrow:last-child{border-bottom:none}
.duk .listrow .lh{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;flex:none;background:var(--surface-2);border:1px solid var(--line);color:var(--teal)}
.duk .listrow .lh .icon{width:18px;height:18px}
.duk .listrow .lb{flex:1;min-width:0}
.duk .listrow .lb b{font-size:13.5px;font-weight:600;display:block;color:var(--ink)}
.duk .listrow .lb span{font-size:12px;color:var(--ink-3)}
.duk .listrow .lr{text-align:right;flex:none}
/* note */
.duk .note{border-left:3px solid var(--teal);background:var(--surface-2);border-radius:0 12px 12px 0;padding:13px 15px;font-size:13.5px;color:var(--ink-2);line-height:1.6}
.duk .note.ai{border-left-color:var(--ai)}
.duk .note .nh{display:flex;align-items:center;gap:8px;font-weight:600;color:var(--ink);margin-bottom:5px;font-size:13px}
.duk .note .nh .icon{width:15px;height:15px}
.duk .note.ai .nh .icon,.duk .note.ai .nh{color:var(--ai)}
/* VAS */
.duk .vas-wrap{padding:6px 2px}
.duk .vas-top{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:14px}
.duk .vas-num{font-family:var(--mono);font-size:46px;font-weight:600;line-height:1;color:var(--ink)}
.duk .vas-face{font-size:13px;font-weight:600;padding:5px 12px;border-radius:999px;color:#fff}
.duk .vas-bar{width:100%;height:10px;border-radius:99px;background:linear-gradient(90deg,#16a34a,#c9820e 55%,#d2453a);position:relative}
.duk .vas-bar i{position:absolute;top:50%;width:24px;height:24px;border-radius:50%;background:#fff;border:3px solid var(--teal);box-shadow:var(--shadow);transform:translate(-50%,-50%)}
.duk .vas-scale{display:flex;justify-content:space-between;font-size:11px;color:var(--ink-3);margin-top:8px}
/* gauge ring */
.duk .gauge{display:flex;align-items:center;gap:18px}
.duk .ring{position:relative;width:128px;height:128px;flex:none}
.duk .ring svg{transform:rotate(-90deg)}
.duk .ring .rtxt{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.duk .ring .rtxt b{font-family:var(--mono);font-size:28px;font-weight:600;line-height:1;color:var(--ink)}
.duk .ring .rtxt span{font-size:11px;color:var(--ink-3);margin-top:2px}
/* bars */
.duk .bars{display:flex;align-items:flex-end;gap:10px;height:130px;padding-top:8px}
.duk .bars .col{flex:1;display:flex;flex-direction:column;align-items:center;gap:7px;height:100%;justify-content:flex-end}
.duk .bars .col .bar{width:62%;border-radius:7px 7px 3px 3px;background:linear-gradient(180deg,var(--teal),var(--teal-strong));min-height:6px}
.duk .bars .col .bar.ai{background:linear-gradient(180deg,var(--ai),#3b45b8)}
.duk .bars .col small{font-size:11px;color:var(--ink-3)}
/* line chart */
.duk .linechart{width:100%;height:auto;display:block}
.duk .lc-area{fill:var(--teal-12)}
.duk .lc-line{fill:none;stroke:var(--teal);stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
.duk .lc-dot{fill:var(--surface);stroke:var(--teal);stroke-width:2.4}
.duk .lc-grid{stroke:var(--line-2);stroke-width:1}
.duk .lc-lbl{fill:var(--ink-3);font-size:10px;font-family:var(--mono)}
/* config rows */
.duk .cfg{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 0;border-bottom:1px solid var(--line-2)}
.duk .cfg:last-child{border-bottom:none}
.duk .cfg .cl b{font-size:13.5px;font-weight:600;display:block;color:var(--ink)}
.duk .cfg .cl span{font-size:11.5px;color:var(--ink-3)}
.duk .chips{display:flex;gap:6px;flex-wrap:wrap}
.duk .chip{padding:6px 12px;border-radius:9px;font-size:12px;font-weight:600;border:1px solid var(--line);background:var(--surface-2);color:var(--ink-2)}
.duk .chip.on{background:var(--teal);color:#fff;border-color:var(--teal)}
.duk .switch{width:46px;height:26px;border-radius:99px;background:var(--surface-3);border:1px solid var(--line);position:relative;flex:none}
.duk .switch::after{content:"";position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:var(--shadow-sm)}
.duk .switch.on{background:var(--teal)}
.duk .switch.on::after{left:auto;right:2px}
/* btn */
.duk .btn-s{height:36px;padding:0 15px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--ink-2);font-size:13px;font-weight:600;display:inline-flex;align-items:center;gap:7px;text-decoration:none}
.duk .btn-s.solid{background:linear-gradient(145deg,var(--teal),var(--teal-strong));color:#fff;border-color:transparent;box-shadow:0 6px 16px var(--teal-50)}
.duk .btn-s.danger{color:var(--danger);border-color:var(--danger-50)}
.duk .btn-s .icon{width:16px;height:16px}
/* dot */
.duk .dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.duk .dot.g{background:#16a34a} .duk .dot.r{background:var(--danger)} .duk .dot.y{background:var(--warn)}
/* log line */
.duk .log-line{display:flex;gap:11px;padding:9px 0;border-bottom:1px solid var(--line-2);font-size:12.5px}
.duk .log-line:last-child{border-bottom:none}
.duk .log-line .t{font-family:var(--mono);color:var(--ink-3);flex:none;font-size:11.5px}
.duk .log-line .m{color:var(--ink-2)}
.duk .log-line .m b{color:var(--ink)}
/* rolebadge */
.duk .rolebadge{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:11.5px;font-weight:600;border:1px solid transparent}
.duk .rolebadge .icon{width:13px;height:13px}
.duk .rb-doctor{background:var(--teal-50);color:var(--teal-strong)}
.duk .rb-ktv{background:rgba(2,132,199,.12);color:#0284c7}
.duk .rb-ncv{background:var(--ai-50);color:var(--ai)}
.duk .rb-qtv{background:var(--warn-50);color:var(--warn)}
.duk .rb-patient{background:rgba(22,163,74,.12);color:#16a34a}
@media (max-width:980px){.duk .g-3{grid-template-columns:repeat(2,1fr)}.duk .g-21,.duk .g-12{grid-template-columns:1fr}}
@media (max-width:760px){.duk .g-3,.duk .g-2{grid-template-columns:1fr}}
"""

def inject_design_system(is_light: bool = True):
    """Inject tokens + component CSS + icon sprite. Gọi mỗi rerun (sau _inject_base_css_once)."""
    tokens = _TOKENS_LIGHT if is_light else _TOKENS_DARK
    st.markdown("<style>" + tokens + _COMPONENT_CSS + "</style>" + _ICON_SPRITE, unsafe_allow_html=True)


# ============================================================ STREAMLIT NATIVE SKIN
# "Thay da" widget gốc của Streamlit (nút, ô nhập, sidebar, card, expander, segmented nav...)
# cho khớp ngôn ngữ thiết kế "clinical-teal" của demo. Dùng var(--token) nên tự đổi theo light/dark.
# PHẢI inject SAU mọi CSS theme cũ (cuối cùng) để thắng độ ưu tiên.
_STREAMLIT_SKIN_CSS = """
<style id="duk-st-skin">
/* ---------- NỀN APP (mesh gradient giống demo) ---------- */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMainViewContainer"]{
  background-color:var(--bg)!important;
  background-image:
    radial-gradient(60vw 50vh at 8% -8%, var(--teal-12), transparent 60%),
    radial-gradient(55vw 50vh at 105% 0%, var(--ai-50), transparent 55%)!important;
  background-attachment:fixed!important;
  color:var(--ink)!important;
}
[data-testid="stAppViewContainer"]>.main .block-container{
  padding-top:0!important;
  padding-bottom:1rem!important;
  max-width:100%!important;
}
/* gọn "chrome": ẩn nút Deploy + toolbar thừa, header trong suốt */
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu{display:none!important;}
header[data-testid="stHeader"]{background:transparent!important;backdrop-filter:none!important;}

/* text mặc định của Streamlit theo theme: light = ink tối, dark = ink sáng */
.stApp, .stApp label, .stApp p, .stApp li,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *{
  color:var(--ink)!important;
}
.stApp small, .stApp caption, [data-testid="stCaptionContainer"],
[data-testid="stMarkdownContainer"] .muted{
  color:var(--ink-3)!important;
}

/* ---------- NÚT BẤM → demo .btn-s / .btn-primary ---------- */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button, .stLinkButton>a{
  border-radius:11px!important;
  border:1px solid var(--line)!important;
  background:var(--surface)!important;
  color:var(--ink-2)!important;
  font-weight:600!important;
  font-family:var(--ui)!important;
  transition:border-color .16s, color .16s, transform .16s, box-shadow .16s!important;
}
.stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover{
  border-color:var(--teal)!important; color:var(--teal)!important; transform:translateY(-1px)!important;
}
.stButton>button *, .stFormSubmitButton>button *, .stDownloadButton>button *, .stLinkButton>a *{
  color:inherit!important;
  -webkit-text-fill-color:inherit!important;
}
/* nút primary → gradient teal */
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primaryFormSubmit"],
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"]{
  background:linear-gradient(145deg,var(--teal),var(--teal-strong))!important;
  color:#fff!important; border:1px solid transparent!important;
  box-shadow:0 6px 16px var(--teal-50)!important;
}
.stButton>button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover{
  transform:translateY(-1px)!important; box-shadow:0 10px 22px var(--teal-50)!important; color:#fff!important;
}

/* ---------- Ô NHẬP (text/number/textarea/select/date) → demo .inp ---------- */
.stTextInput div[data-baseweb="input"], .stNumberInput div[data-baseweb="input"],
.stTextArea div[data-baseweb="textarea"], .stTextArea div[data-baseweb="base-input"],
.stDateInput div[data-baseweb="input"],
.stSelectbox div[data-baseweb="select"]>div, .stMultiSelect div[data-baseweb="select"]>div{
  background:var(--surface-2)!important;
  border:1px solid var(--line)!important;
  border-radius:11px!important;
  transition:border-color .16s, box-shadow .16s!important;
}
.stTextInput div[data-baseweb="input"]:focus-within, .stNumberInput div[data-baseweb="input"]:focus-within,
.stTextArea div[data-baseweb="textarea"]:focus-within, .stDateInput div[data-baseweb="input"]:focus-within,
.stSelectbox div[data-baseweb="select"]:focus-within>div{
  border-color:var(--teal)!important; box-shadow:0 0 0 3px var(--teal-50)!important; background:var(--surface)!important;
}
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input{
  color:var(--ink)!important; background:transparent!important;
}
/* nhãn input */
.stTextInput label, .stNumberInput label, .stTextArea label, .stSelectbox label,
.stMultiSelect label, .stDateInput label, .stSlider label, .stRadio label, .stCheckbox label{
  color:var(--ink-2)!important; font-weight:600!important;
}

/* ---------- SIDEBAR → mặt demo ---------- */
[data-testid="stSidebar"]{
  background:var(--surface)!important; border-right:1px solid var(--line)!important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3{
  color:var(--ink)!important; font-family:var(--display)!important;
}

/* ---------- CONTAINER có viền + EXPANDER → demo .card ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(>div>[data-testid="stVerticalBlock"]){border-radius:var(--r)!important;}
div[data-testid="stExpander"]{
  border:1px solid var(--line)!important; border-radius:var(--r)!important;
  background:var(--surface)!important; box-shadow:var(--shadow-sm)!important; overflow:hidden!important;
}
div[data-testid="stExpander"] summary{color:var(--ink)!important; font-weight:600!important;}
div[data-testid="stExpander"] summary:hover{color:var(--teal)!important;}

/* ---------- THANH ĐIỀU HƯỚNG (segmented_control) → demo nav pills ---------- */
div[data-testid="stSegmentedControl"] button{
  border-radius:11px!important; border:1px solid var(--line)!important;
  background:var(--surface)!important; color:var(--ink-2)!important; font-weight:600!important;
}
div[data-testid="stSegmentedControl"] button:hover{border-color:var(--teal)!important; color:var(--teal)!important;}
div[data-testid="stSegmentedControl"] button[aria-checked="true"],
div[data-testid="stSegmentedControl"] button[kind="segmented_controlActive"]{
  background:linear-gradient(145deg,var(--teal),var(--teal-strong))!important;
  color:#fff!important; border-color:transparent!important; box-shadow:0 6px 16px var(--teal-50)!important;
}

/* ---------- TABS (st.tabs) → gạch chân teal ---------- */
.stTabs [data-baseweb="tab-list"]{border-bottom:1px solid var(--line)!important;}
.stTabs [data-baseweb="tab"]{color:var(--ink-3)!important; font-weight:600!important;}
.stTabs [data-baseweb="tab"][aria-selected="true"]{color:var(--teal-strong)!important;}
.stTabs [data-baseweb="tab-highlight"]{background:var(--teal)!important;}

/* ---------- SLIDER / TOGGLE / CHECKBOX accent teal ---------- */
.stSlider [data-baseweb="slider"] div[role="slider"]{background:var(--teal)!important;}
[data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"]{color:var(--ink-3)!important;}

/* ---------- ALERTS (info/success/warning/error) bo góc mềm ---------- */
[data-testid="stAlert"]{border-radius:var(--r)!important;}

/* caption + markdown text màu theo token */
[data-testid="stCaptionContainer"]{color:var(--ink-3)!important;}
</style>
"""


def inject_streamlit_skin(is_light: bool = True):
    """Skin widget gốc Streamlit theo demo. Gọi mỗi rerun, SAU mọi CSS theme cũ (cuối cùng)."""
    st.markdown(_STREAMLIT_SKIN_CSS, unsafe_allow_html=True)


# ============================================================ HTML HELPERS (port từ JS demo)
def _icon(i, cls="icon"):
    return f'<svg class="{cls}"><use href="#{_ic(i)}"/></svg>'

def block(inner_html: str) -> str:
    """Bọc nội dung trong wrapper .duk để CSS có hiệu lực. Dùng cho mỗi st.markdown."""
    return f'<div class="duk">{inner_html}</div>'

def page_head(title, sub, actions="") -> str:
    return (f'<div class="duk"><div class="page-head"><div><h1>{title}</h1>'
            f'<div class="sub">{sub}</div></div><div class="actions">{actions}</div></div></div>')

def stat(icon, label, val, trend="", dir="", sub="") -> str:
    tri = "▲" if dir == "up" else "▼"
    trend_html = f'<span class="trend {dir}">{tri} {trend}</span>' if trend else ""
    sub_html = f" · {sub}" if sub else ""
    return (f'<div class="stat"><div class="top"><div class="ico">{_icon(icon)}</div>{trend_html}</div>'
            f'<div class="v">{val}</div><div class="l">{label}{sub_html}</div></div>')

def pill(text, cls="neu", icon="") -> str:
    return f'<span class="pill {cls}">{_icon(icon) if icon else ""} {text}</span>'

def ring(pct, label, sub, cls="") -> str:
    r = 54
    c = 2 * math.pi * r
    off = c * (1 - pct / 100)
    col = {"ai": "var(--ai)", "warn": "var(--warn)", "bad": "var(--danger)"}.get(cls, "var(--teal)")
    return (f'<div class="ring"><svg width="128" height="128" viewBox="0 0 128 128">'
            f'<circle cx="64" cy="64" r="{r}" fill="none" stroke="var(--surface-3)" stroke-width="11"/>'
            f'<circle cx="64" cy="64" r="{r}" fill="none" stroke="{col}" stroke-width="11" stroke-linecap="round" '
            f'stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}"/></svg>'
            f'<div class="rtxt"><b>{label}</b><span>{sub}</span></div></div>')

def line_chart(pts, labels) -> str:
    W, H, pad = 520, 170, 26
    mx = max(pts) * 1.12 if pts else 1
    mn = 0
    n = len(pts)
    x = lambda i: pad + (i * (W - pad * 2) / (n - 1)) if n > 1 else pad
    y = lambda v: H - pad - ((v - mn) / (mx - mn)) * (H - pad * 1.6) if mx > mn else H - pad
    line = " ".join(f'{"M" if i == 0 else "L"}{x(i):.1f} {y(p):.1f}' for i, p in enumerate(pts))
    area = f'{line} L{x(n-1):.1f} {H-pad} L{pad} {H-pad} Z'
    grid = "".join(f'<line class="lc-grid" x1="{pad}" y1="{pad*.6+g*(H-pad*1.6):.1f}" x2="{W-pad}" y2="{pad*.6+g*(H-pad*1.6):.1f}"/>' for g in (0, .5, 1))
    dots = "".join(f'<circle class="lc-dot" cx="{x(i):.1f}" cy="{y(p):.1f}" r="3.6"/>' for i, p in enumerate(pts))
    labs = "".join(f'<text class="lc-lbl" x="{x(i):.1f}" y="{H-7}" text-anchor="middle">{l}</text>' for i, l in enumerate(labels))
    return f'<svg class="linechart" viewBox="0 0 {W} {H}">{grid}<path class="lc-area" d="{area}"/><path class="lc-line" d="{line}"/>{dots}{labs}</svg>'

def bar_chart(data) -> str:
    mx = max(d["v"] for d in data) if data else 1
    cols = "".join(
        f'<div class="col"><div class="bar {"ai" if d.get("ai") else ""}" style="height:{d["v"]/mx*100:.0f}%" title="{d["v"]}"></div>'
        f'<small>{d["l"]}</small></div>' for d in data)
    return f'<div class="bars">{cols}</div>'

def note(title, body, icon="i-stetho", ai=False) -> str:
    return (f'<div class="note {"ai" if ai else ""}"><div class="nh">{_icon(icon)} {title}</div>{body}</div>')

def section_label(text, icon) -> str:
    return f'<div class="section-label">{_icon(icon)} {text}</div>'

def card_open(title, icon="i-chart", right="") -> str:
    return f'<div class="card"><div class="card-h">{_icon(icon)}<h3>{title}</h3>{right}</div><div class="card-b">'

def card_close() -> str:
    return "</div></div>"

def seg_row(t, d, cls, pct) -> str:
    try:
        w = int("".join(ch for ch in str(pct) if ch.isdigit()) or 70)
    except ValueError:
        w = 70
    mcls = "" if cls == "ok" else cls
    return (f'<div style="margin-bottom:13px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">'
            f'<b style="font-size:13.5px;color:var(--ink)">{t}</b><span class="pill {cls}">{pct}</span></div>'
            f'<div class="meter {mcls}"><i style="width:{w}%"></i></div>'
            f'<span class="muted" style="font-size:12px">{d}</span></div>')

def vas_row(date, v, face, cls) -> str:
    return (f'<div class="listrow"><div class="lh">{_icon("i-vas")}</div>'
            f'<div class="lb"><b>{date}</b><span>{face}</span></div>'
            f'<div class="lr"><span class="pill {cls}" style="font-family:var(--mono)">{v}/10</span></div></div>')

def sched_row(day, time, ex, state) -> str:
    m = {"done": ("ok", "Đã tập", "i-check"), "today": ("ai", "Hôm nay", "i-clock"), "soon": ("neu", "Sắp tới", "i-bell")}
    c, l, i = m.get(state, m["soon"])
    return (f'<div class="listrow"><div class="lh">{_icon("i-cal")}</div>'
            f'<div class="lb"><b>{day} · {time}</b><span>{ex}</span></div>'
            f'<div class="lr"><span class="pill {c}">{_icon(i)} {l}</span></div></div>')

def pat_row(name, ini, dx, vas, rom, cls, status) -> str:
    scls = "ok" if cls == "ok" else "neu"
    return (f'<tr class="hl"><td><div class="who"><div class="av" style="background:var(--teal)">{ini}</div>'
            f'<div><b>{name}</b><br><span>{dx}</span></div></div></td><td>{dx}</td>'
            f'<td><span class="pill {cls}" style="font-family:var(--mono)">{vas}</span></td>'
            f'<td class="mono">{rom}</td><td><span class="pill {scls}">{status}</span></td>'
            f'<td><span class="btn-s">{_icon("i-arrow")}</span></td></tr>')

def cmp_row(name, ex, clin, ai, diff, cls) -> str:
    return (f'<tr class="hl"><td><b style="color:var(--ink)">{name}</b></td><td>{ex}</td>'
            f'<td class="mono">{clin}</td><td class="mono" style="color:var(--ai)">{ai}</td>'
            f'<td class="mono">{diff}</td><td><span class="pill {cls}">{"Khớp tốt" if cls == "ok" else "Cần xem"}</span></td></tr>')

def proto(name, desc, freq) -> str:
    return (f'<div class="listrow"><div class="lh">{_icon("i-dumbbell")}</div>'
            f'<div class="lb"><b>{name}</b><span>{desc}</span></div>'
            f'<div class="lr"><span class="pill neu">{freq}</span></div></div>')

def queue_row(name, ex, vas, cls, ago) -> str:
    return (f'<div class="listrow"><div class="lh">{_icon("i-video")}</div>'
            f'<div class="lb"><b>{name}</b><span>{ex} · {ago}</span></div>'
            f'<div class="lr" style="display:flex;gap:8px;align-items:center"><span class="pill {cls}" style="font-family:var(--mono)">{vas}</span>'
            f'<span class="btn-s solid">{_icon("i-arrow")}</span></div></div>')

def svc_row(name, status, dot="g") -> str:
    return (f'<div class="listrow"><div class="lb"><b>{name}</b><span>{status}</span></div>'
            f'<div class="lr"><span class="pill ok"><span class="dot {dot}"></span> Online</span></div></div>')

def log_row(t, who, action, target) -> str:
    return f'<div class="log-line"><span class="t">{t}</span><span class="m"><b>@{who}</b> {action} <b>{target}</b></span></div>'

def acc_row(name, acc, role, badge, icon, dot, last) -> str:
    ini = "".join(w[0] for w in name.split(".")[-1].strip().split(" ")[-2:]).upper()
    act = "Hoạt động" if dot == "g" else "Chờ duyệt"
    btn = (f'<span class="btn-s solid">{_icon("i-check")}Duyệt</span>' if dot == "y"
           else f'<span class="btn-s">{_icon("i-cog")}</span>')
    return (f'<tr class="hl"><td><div class="who"><div class="av">{ini}</div>'
            f'<div><b>{name}</b><br><span class="mono">@{acc}</span></div></div></td>'
            f'<td><span class="rolebadge {badge}">{_icon(icon)} {role}</span></td>'
            f'<td><span class="dot {dot}"></span> {act}</td><td class="muted">{last}</td><td>{btn}</td></tr>')

def vas_display(value: int) -> str:
    faces = [("Không đau", "#16a34a"), ("Rất nhẹ", "#16a34a"), ("Nhẹ", "#16a34a"), ("Nhẹ", "#65a30d"),
             ("Đau vừa", "#c9820e"), ("Đau vừa", "#c9820e"), ("Đau nhiều", "#ea580c"), ("Đau nhiều", "#dc2626"),
             ("Dữ dội", "#dc2626"), ("Dữ dội", "#b91c1c"), ("Tối đa", "#991b1b")]
    value = max(0, min(10, int(value)))
    txt, col = faces[value]
    return (f'<div class="vas-wrap"><div class="vas-top"><div class="vas-num" style="color:{col}">{value}</div>'
            f'<div class="vas-face" style="background:{col}">{txt}</div></div>'
            f'<div class="vas-bar"><i style="left:{value/10*100:.0f}%"></i></div>'
            f'<div class="vas-scale"><span>0 · Không đau</span><span>10 · Đau dữ dội</span></div></div>')

def table(headers, rows_html) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    return f'<table class="tbl"><thead><tr>{th}</tr></thead><tbody>{rows_html}</tbody></table>'

def kv(label, value, color="") -> str:
    style = f' style="color:{color}"' if color else ""
    return f'<div class="kv"><span>{label}</span><b{style}>{value}</b></div>'

# ============================================================ AUTH SCREEN COMPONENTS
def auth_screen_html() -> str:
    """Màn hình đăng nhập/đăng ký giống demo HTML."""
    return """
<div class="auth-hero">
  <span class="eyebrow"><svg class="icon sm"><use href="#i-shield-c"/></svg> Clinical-Grade · Giám sát từ xa bằng Thị giác máy tính</span>
  <div class="auth-hero-title" role="heading" aria-level="1" style="display:block!important;margin:0!important;max-width:30ch!important;font-family:var(--display,'Fraunces',Georgia,serif)!important;font-size:clamp(48px,4vw,58px)!important;line-height:1.04!important;font-weight:600!important;letter-spacing:0!important;color:var(--ink,#111827)!important;text-wrap:wrap!important;word-break:keep-all!important;overflow-wrap:normal!important;hyphens:none!important;font-kerning:normal!important;">
    <span class="auth-word">Giám</span> <span class="auth-word">sát</span> <span class="auth-word">tập</span> <em style="font-family:inherit!important;font-size:inherit!important;line-height:inherit!important;font-weight:inherit!important;font-style:italic!important;color:var(--teal,#1d6fe8)!important;"><span class="auth-word">phục</span> <span class="auth-word">hồi</span> <span class="auth-word">chức</span> <span class="auth-word">năng</span></em> <span class="auth-word">bằng</span><br/><span class="auth-word">AI,</span> <span class="auth-word">ngay</span> <span class="auth-word">tại</span> <span class="auth-word">nhà.</span>
  </div>
  <p class="lede">Bệnh nhân khai báo triệu chứng (VAS) → AI phân tích khung xương & góc khớp theo thời gian thực → Chuyên gia đối chiếu và đưa ra phác đồ. Một luồng lâm sàng khép kín.</p>
  <div class="hero-stats">
    <div class="hstat"><div class="n">33</div><div class="l">điểm khung xương / khung hình</div></div>
    <div class="hstat"><div class="n">±15°</div><div class="l">sai số mục tiêu giai đoạn 3</div></div>
    <div class="hstat"><div class="n">5</div><div class="l">vai trò người dùng</div></div>
  </div>
  <div class="pose-card" aria-hidden="true">
    <svg class="pose-svg" viewBox="0 0 240 260">
      <line x1="120" y1="92" x2="210" y2="92" stroke="var(--ink-3)" stroke-width="2" stroke-dasharray="5 6" opacity=".5"/>
      <path class="pose-arc" d="M150 92 A30 30 0 0 0 132 64"/>
      <text x="158" y="80" fill="var(--ai)" font-family="var(--mono)" font-size="13" font-weight="600">128°</text>
      <circle cx="120" cy="40" r="16" class="pose-joint"/>
      <line x1="120" y1="56" x2="120" y2="150" class="pose-bone"/>
      <line x1="120" y1="92" x2="86" y2="138" class="pose-bone dim"/>
      <line x1="86" y1="138" x2="74" y2="178" class="pose-bone dim"/>
      <circle cx="86" cy="138" r="6" class="pose-joint dim"/>
      <g id="poseArm">
        <line x1="120" y1="92" x2="170" y2="118" class="pose-bone">
          <animate attributeName="x2" values="170;150;170" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
          <animate attributeName="y2" values="118;78;118" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
        </line>
        <line x1="170" y1="118" x2="206" y2="132" class="pose-bone">
          <animate attributeName="x1" values="170;150;170" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
          <animate attributeName="y1" values="118;78;118" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
          <animate attributeName="x2" values="206;186;206" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
          <animate attributeName="y2" values="132;58;132" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
        </line>
        <circle cx="170" cy="118" r="6" class="pose-joint">
          <animate attributeName="cx" values="170;150;170" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
          <animate attributeName="cy" values="118;78;118" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
        </circle>
        <circle cx="206" cy="132" r="5.5" class="pose-joint">
          <animate attributeName="cx" values="206;186;206" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
          <animate attributeName="cy" values="132;58;132" keyTimes="0;0.5;1" dur="4.4s" repeatCount="indefinite"/>
        </circle>
      </g>
      <circle cx="120" cy="92" r="7" class="pose-joint"/>
      <line x1="120" y1="150" x2="100" y2="214" class="pose-bone"/>
      <line x1="120" y1="150" x2="140" y2="214" class="pose-bone"/>
      <circle cx="120" cy="150" r="6" class="pose-joint"/>
      <circle cx="100" cy="214" r="5.5" class="pose-joint"/>
      <circle cx="140" cy="214" r="5.5" class="pose-joint"/>
    </svg>
  </div>
</div>
"""

def topbar_html(user_info=None, is_light=True) -> str:
    """Top bar với brand và user info giống demo."""
    user_html = ""
    if user_info:
        role_badges = {
            "Bệnh nhân": ("rb-patient", "i-heart", "BN"),
            "Bác sĩ / KTV PHCN": ("rb-doctor", "i-stetho", "BS"),
            "Nghiên cứu viên": ("rb-ncv", "i-micro", "NC"),
            "Quản trị viên": ("rb-qtv", "i-cog", "QT")
        }
        badge_cls, icon, av = role_badges.get(user_info.get("role", ""), ("rb-patient", "i-heart", "BN"))
        user_html = f"""
<div id="userArea" style="display:flex;align-items:center;gap:12px">
  <span class="rolebadge {badge_cls}"><svg class="icon"><use href="#{icon}"/></svg> {user_info.get('role', '')}</span>
  <div class="userchip">
    <div class="avatar">{av}</div>
    <div class="meta"><span class="nm">{user_info.get('full_name', '')}</span><span class="rl">{user_info.get('role', '')}</span></div>
  </div>
</div>"""

    return f"""
<header class="topbar">
  <div class="brand">
    <div class="brand-mark"><svg class="icon"><use href="#i-pulse"/></svg></div>
    <div class="brand-txt">
      <span class="brand-name">Rehab <b>AI</b> Monitor</span>
      <span class="brand-sub">Hệ sinh thái lâm sàng · HUPH × BV Phạm Ngọc Thạch · 2026</span>
    </div>
  </div>
  <div class="spacer"></div>
  {user_html}
</header>
"""

def sidebar_nav_html(role: str, current_page: str = "") -> str:
    """Navigation sidebar theo vai trò giống demo."""
    nav_items = {
        "Bệnh nhân": [
            ("train", "Tập luyện hôm nay", "i-dumbbell"),
            ("feedback", "Nhận xét AI & Bác sĩ", "i-spark"),
            ("progress", "Tiến triển ROM", "i-chart"),
            ("vas", "Khai báo VAS", "i-vas"),
            ("schedule", "Lịch nhắc nhở", "i-bell")
        ],
        "Bác sĩ / KTV PHCN": [
            ("patients", "Danh sách bệnh nhân", "i-users"),
            ("evaluate", "Đánh giá lâm sàng", "i-stetho"),
            ("compare", "Đối chiếu kết quả AI", "i-target"),
            ("protocol", "Phác đồ điều trị", "i-doc")
        ],
        "Nghiên cứu viên": [
            ("dataset", "Quản lý Dataset", "i-db"),
            ("model", "Cấu hình mô hình AI", "i-cog"),
            ("metrics", "AI vs Lâm sàng", "i-bars"),
            ("analysis", "Phân tích kỹ thuật", "i-flask")
        ],
        "Quản trị viên": [
            ("accounts", "Quản lý tài khoản", "i-users"),
            ("system", "Tình trạng hệ thống", "i-shield"),
            ("cleanup", "Dọn dẹp CSDL", "i-broom"),
            ("logs", "Nhật ký hoạt động", "i-log")
        ]
    }

    items = nav_items.get(role, [])
    nav_html = "".join(
        f'<button class="navitem {"on" if page_id == current_page else ""}" onclick="goNav(\'{page_id}\')">'
        f'<svg class="icon"><use href="#{icon}"/></svg><span>{label}</span></button>'
        for page_id, label, icon in items
    )

    return f'<div class="side-section">Điều hướng</div><nav id="navList">{nav_html}</nav>'

def side_info_html(role: str, user_info=None, stats=None) -> str:
    """Side card với thông tin tóm tắt theo vai trò."""
    stats = stats or {}
    if role == "Bệnh nhân":
        diagnosis = stats.get("diagnosis") or "Chưa khai báo"
        treatment_week = stats.get("treatment_week") or "Theo dữ liệu hệ thống"
        latest_vas = stats.get("latest_vas") or "N/A"
        doctor = stats.get("doctor") or "Chưa gán"
        return f"""
<div class="side-card">
  <div class="h"><svg class="icon"><use href="#i-heart"/></svg> Hồ sơ của tôi</div>
  <div class="kv"><span>Chẩn đoán</span><b>{diagnosis}</b></div>
  <div class="kv"><span>Tuần điều trị</span><b>{treatment_week}</b></div>
  <div class="kv"><span>VAS gần nhất</span><b style="color:var(--warn)">{latest_vas}</b></div>
  <div class="kv"><span>Bác sĩ phụ trách</span><b>{doctor}</b></div>
</div>"""
    elif role in ["Bác sĩ / KTV PHCN"]:
        total_patients = stats.get("total_patients", 0)
        pending_eval = stats.get("pending_eval", 0)
        vas_high = stats.get("vas_high", 0)
        sessions_7d = stats.get("sessions_7d", 0)
        return f"""
<div class="side-card">
  <div class="h"><svg class="icon"><use href="#i-users"/></svg> Tổng quan hôm nay</div>
  <div class="kv"><span>BN phụ trách</span><b>{total_patients}</b></div>
  <div class="kv"><span>Chờ đánh giá</span><b style="color:var(--danger)">{pending_eval}</b></div>
  <div class="kv"><span>VAS ≥ 6 (cảnh báo)</span><b style="color:var(--warn)">{vas_high}</b></div>
  <div class="kv"><span>Buổi tập 7 ngày</span><b>{sessions_7d}</b></div>
</div>"""
    elif role == "Nghiên cứu viên":
        total_videos = stats.get("total_videos", 0)
        pending_ai = stats.get("pending_ai", 0)
        model = stats.get("model", "MP-Heavy")
        avg_acc = stats.get("avg_acc", 0)
        return f"""
<div class="side-card">
  <div class="h"><svg class="icon"><use href="#i-db"/></svg> Dataset hiện hành</div>
  <div class="kv"><span>Video mẫu</span><b>{total_videos}</b></div>
  <div class="kv"><span>Chờ AI xử lý</span><b>{pending_ai}</b></div>
  <div class="kv"><span>Mô hình</span><b>{model}</b></div>
  <div class="kv"><span>Độ chính xác TB</span><b style="color:var(--ok)">{avg_acc}</b></div>
</div>"""
    else:  # Quản trị viên
        accounts = stats.get("accounts", 0)
        sync = stats.get("sync", "Local")
        storage = stats.get("storage", "Local")
        status = stats.get("status", "OK")
        return f"""
<div class="side-card">
  <div class="h"><svg class="icon"><use href="#i-shield"/></svg> Hệ thống</div>
  <div class="kv"><span>Tài khoản</span><b>{accounts}</b></div>
  <div class="kv"><span>Lưu trữ</span><b>{storage}</b></div>
  <div class="kv"><span>Đồng bộ</span><b>{sync}</b></div>
  <div class="kv"><span>Trạng thái</span><b style="color:var(--ok)">{status}</b></div>
</div>"""

# ============================================================ ADDITIONAL CSS FOR AUTH & NAV
_AUTH_NAV_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,600..700,50,1&family=Inter:wght@400;500;600;700&display=swap');
/* Icons used outside the .duk content wrapper: auth hero, topbar, badges. */
.icon{
  width:18px!important;
  height:18px!important;
  fill:none!important;
  stroke:currentColor!important;
  stroke-width:1.7!important;
  stroke-linecap:round!important;
  stroke-linejoin:round!important;
  flex:none!important;
  vertical-align:middle!important;
}
.icon.sm{width:15px!important;height:15px!important}
.icon.lg{width:26px!important;height:26px!important}
.icon.xl{width:34px!important;height:34px!important}
.stApp:has(.auth-shell-anchor),
.stApp:has(.auth-shell-anchor) [data-testid="stAppViewContainer"]{
  background-color:var(--bg)!important;
  background-image:
    radial-gradient(60vw 50vh at 8% -8%,var(--bg-mesh-1),transparent 60%),
    radial-gradient(55vw 50vh at 105% 0%,var(--bg-mesh-2),transparent 55%)!important;
  background-attachment:fixed!important;
  color:var(--ink)!important;
}
.stApp:has(.auth-shell-anchor) [data-testid="stAppViewContainer"]>.main .block-container{
  padding:0!important;
  max-width:100%!important;
  width:100%!important;
  margin:0!important;
}
.stApp:has(.auth-shell-anchor) [data-testid="stMain"],
.stApp:has(.auth-shell-anchor) section.main,
.stApp:has(.auth-shell-anchor) .main,
.stApp:has(.auth-shell-anchor) div.block-container,
.stApp:has(.auth-shell-anchor) [data-testid="stMainBlockContainer"],
.stApp:has(.auth-shell-anchor) [data-testid="stAppViewBlockContainer"]{
  margin-top:0!important;
  padding-top:0!important;
}
.stApp:has(.auth-shell-anchor) [data-testid="stVerticalBlock"],
.stApp:has(.auth-shell-anchor) [data-testid="stVerticalBlockBorderWrapper"]{
  row-gap:0!important;
}
.stApp:has(.auth-shell-anchor) .element-container:has(.topbar),
.stApp:has(.auth-shell-anchor) [data-testid="stMarkdownContainer"]:has(.topbar){
  margin:0!important;
  padding:0!important;
}
.stApp:has(.auth-shell-anchor) [data-testid="stAppViewBlockContainer"]{
  padding-top:0!important;
}
.stApp:has(.auth-shell-anchor) [data-testid="stMarkdownContainer"],
.stApp:has(.auth-shell-anchor) [data-testid="stMarkdownContainer"] *,
.stApp:has(.auth-shell-anchor) label,
.stApp:has(.auth-shell-anchor) label *,
.stApp:has(.auth-shell-anchor) p,
.stApp:has(.auth-shell-anchor) span,
.stApp:has(.auth-shell-anchor) h1,
.stApp:has(.auth-shell-anchor) h2{
  color:inherit;
}
/* ============================================================ AUTH SCREEN */
.auth-shell-anchor{
  display:block!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
  color:var(--ink)!important;
}
.auth-layout-row-anchor{
  display:block!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
.auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"],
.stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit){
  display:grid!important;
  grid-template-columns:minmax(0,1fr) minmax(360px,430px)!important;
  align-items:start!important;
  column-gap:clamp(54px,8vw,168px)!important;
  width:100%!important;
  padding:clamp(138px,18vh,208px) clamp(64px,3.5vw,82px) clamp(32px,5vh,58px)!important;
}
.auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
.stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit) > div[data-testid="stColumn"]{
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
  flex:unset!important;
}
.auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child,
.stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit) > div[data-testid="stColumn"]:first-child{
  grid-column:1!important;
}
.auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child,
.stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit) > div[data-testid="stColumn"]:last-child{
  grid-column:2!important;
  justify-self:stretch!important;
}
.auth-shell-anchor + div{
  margin-top:0!important;
  padding-top:0!important;
}
.st-key-auth_card_streamlit{
  margin-top:0!important;
}
.st-key-auth_card_streamlit [data-testid="stVerticalBlock"]{
  margin-top:0!important;
}
.st-key-auth_theme_icon_button{
  position:fixed;
  top:10px;
  right:28px;
  z-index:1000;
  width:38px!important;
  height:38px!important;
  pointer-events:auto!important;
}
.st-key-auth_theme_icon_button .stButton>button,
.st-key-auth_theme_icon_button button{
  width:38px!important;
  height:38px!important;
  min-height:38px!important;
  padding:0!important;
  border-radius:11px!important;
  display:grid!important;
  place-items:center!important;
  background:var(--surface)!important;
  border:1px solid var(--line)!important;
  color:var(--ink-2)!important;
  box-shadow:none!important;
  font-size:20px!important;
  line-height:1!important;
}
.st-key-auth_theme_icon_button .stButton>button *,
.st-key-auth_theme_icon_button button *{
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
}
.st-key-auth_theme_icon_button .stButton>button:hover,
.st-key-auth_theme_icon_button button:hover{
  border-color:var(--teal)!important;
  color:var(--teal)!important;
  transform:translateY(-1px)!important;
}
.st-key-app_logout_icon_button,
.st-key-app_theme_icon_button{
  position:fixed!important;
  top:12px!important;
  z-index:2147483000!important;
  width:38px!important;
  height:38px!important;
  pointer-events:auto!important;
}
.st-key-app_logout_icon_button{right:72px!important}
.st-key-app_theme_icon_button{right:28px!important}
.st-key-app_logout_icon_button *,
.st-key-app_theme_icon_button *{
  pointer-events:auto!important;
}
.st-key-app_logout_icon_button .stButton>button,
.st-key-app_theme_icon_button .stButton>button,
.st-key-app_logout_icon_button button,
.st-key-app_theme_icon_button button{
  width:38px!important;
  height:38px!important;
  min-height:38px!important;
  padding:0!important;
  border-radius:11px!important;
  display:grid!important;
  place-items:center!important;
  background:var(--surface)!important;
  border:1px solid var(--line)!important;
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
  box-shadow:none!important;
  font-size:18px!important;
  line-height:1!important;
}
.st-key-app_logout_icon_button .stButton>button *,
.st-key-app_theme_icon_button .stButton>button *,
.st-key-app_logout_icon_button button *,
.st-key-app_theme_icon_button button *{
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
}
.st-key-app_logout_icon_button .stButton>button:hover,
.st-key-app_logout_icon_button button:hover{
  border-color:var(--danger)!important;
  color:var(--danger)!important;
  -webkit-text-fill-color:var(--danger)!important;
  transform:translateY(-1px)!important;
}
.st-key-app_theme_icon_button .stButton>button:hover,
.st-key-app_theme_icon_button button:hover{
  border-color:var(--teal)!important;
  color:var(--teal)!important;
  -webkit-text-fill-color:var(--teal)!important;
  transform:translateY(-1px)!important;
}
.auth-wrap{
  min-height:calc(100vh - 63px);
  display:grid;grid-template-columns:1.05fr .95fr;
  align-items:stretch;
}
.auth-hero{
  position:relative;overflow:hidden;
  padding:0 0 0 0;
  display:flex;flex-direction:column;justify-content:center;gap:24px;
  min-height:650px;
  color:var(--ink)!important;
}
.auth-hero .eyebrow,
[data-testid="stMarkdownContainer"] .auth-hero .eyebrow{
  display:inline-flex;align-items:center;gap:8px;align-self:flex-start;
  padding:8px 16px;border-radius:999px;
  font-family:var(--ui)!important;
  font-size:16px!important;
  line-height:1.2!important;
  font-weight:700;letter-spacing:0!important;
  background:var(--teal-50);color:var(--teal-strong)!important;border:1px solid var(--teal-50);
  -webkit-text-fill-color:var(--teal-strong)!important;
}
.stApp:has(.auth-shell-anchor) [data-testid="stMarkdownContainer"] .auth-hero .eyebrow,
.stApp:has(.auth-shell-anchor) [data-testid="stMarkdownContainer"] .auth-hero .eyebrow *{
  color:var(--teal-strong)!important;
  -webkit-text-fill-color:var(--teal-strong)!important;
}
.auth-hero h1,
.auth-hero .auth-hero-title,
[data-testid="stMarkdownContainer"] .auth-hero h1,
[data-testid="stMarkdownContainer"] .auth-hero .auth-hero-title{
  display:block!important;
  visibility:visible!important;
  font-family:var(--display,'Fraunces',Georgia,serif)!important;
  font-weight:600!important;
  font-size:clamp(48px,4vw,58px)!important;
  line-height:1.04!important;
  margin:0!important;
  letter-spacing:0!important;
  color:var(--ink)!important;
  max-width:30ch!important;
  text-wrap:wrap!important;
  word-break:keep-all!important;
  overflow-wrap:normal!important;
  hyphens:none!important;
  font-kerning:normal!important;
}
.auth-hero .auth-hero-title br,
[data-testid="stMarkdownContainer"] .auth-hero .auth-hero-title br{
  display:block!important;
}
.auth-hero h1 em,
.auth-hero .auth-hero-title em,
[data-testid="stMarkdownContainer"] .auth-hero h1 em,
[data-testid="stMarkdownContainer"] .auth-hero .auth-hero-title em{
  font-family:inherit!important;
  font-size:inherit!important;
  line-height:inherit!important;
  font-weight:inherit!important;
  font-style:italic;
  color:var(--teal)!important;
  white-space:normal!important;
}
.auth-hero .auth-hero-title .auth-word,
[data-testid="stMarkdownContainer"] .auth-hero .auth-hero-title .auth-word{
  display:inline-block!important;
  font-family:inherit!important;
  font-size:inherit!important;
  line-height:inherit!important;
  font-weight:inherit!important;
  letter-spacing:0!important;
  word-break:keep-all!important;
  overflow-wrap:normal!important;
  hyphens:none!important;
  white-space:nowrap!important;
}
.auth-hero p.lede,
[data-testid="stMarkdownContainer"] .auth-hero p.lede{
  font-family:var(--ui)!important;
  font-size:16px!important;
  line-height:1.6!important;
  color:var(--ink-2)!important;
  max-width:48ch;
  margin:0!important;
}
.hero-stats{display:flex;gap:14px;flex-wrap:wrap}
.hstat{
  background:var(--surface);border:1px solid var(--line);border-radius:var(--r);
  padding:14px 16px;min-width:130px;box-shadow:var(--shadow-sm);
}
.hstat .n{font-family:var(--mono);font-size:23px;font-weight:600;color:var(--teal-strong)}
.hstat .l{font-size:12px;color:var(--ink-3)!important;margin-top:3px}
.pose-card{
  position:absolute;right:0;bottom:0;width:min(34vw,300px);opacity:.9;pointer-events:none;
}
.pose-svg{width:100%;height:auto;overflow:visible}
.pose-bone{stroke:var(--teal);stroke-width:5;stroke-linecap:round;fill:none}
.pose-bone.dim{stroke:var(--ink-3);opacity:.35}
.pose-joint{fill:var(--surface);stroke:var(--teal);stroke-width:3.4}
.pose-joint.dim{stroke:var(--ink-3);opacity:.45}
.pose-arc{stroke:var(--ai);stroke-width:4;fill:none;stroke-linecap:round;opacity:.85}

.auth-card-streamlit,
.st-key-auth_card_streamlit{
  width:100%;max-width:460px;margin:0;
  align-self:flex-start!important;
}
.auth-card-head{
  display:none;
}
.st-key-auth_card_streamlit{
  background:var(--surface)!important;
  border:1px solid var(--line)!important;
  border-radius:var(--r-lg)!important;
  box-shadow:var(--shadow-lg)!important;
  padding:38px 36px 34px!important;
  color:var(--ink)!important;
}
.st-key-auth_card_streamlit [data-testid="stVerticalBlockBorderWrapper"],
.st-key-auth_card_streamlit [data-testid="stVerticalBlockBorderWrapper"] > div{
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
  padding:0!important;
}
.auth-card-title h2{
  font-family:var(--display,'Fraunces',Georgia,serif)!important;
  font-weight:600!important;
  font-size:27px!important;
  line-height:1.08!important;
  letter-spacing:0!important;
  color:var(--ink)!important;
  margin:0 0 8px!important;
}
.auth-card-title p{
  font-family:var(--ui,'Inter','Be Vietnam Pro',system-ui,sans-serif)!important;
  color:var(--ink-3)!important;
  font-size:13.5px!important;
  line-height:1.45!important;
  margin:0 0 24px!important;
}
.st-key-auth_card_streamlit [data-testid="stSelectbox"]{
  margin-bottom:14px!important;
}
.st-key-auth_card_streamlit .stTabs [data-baseweb="tab-list"]{
  display:flex;gap:4px;background:var(--surface-2)!important;border:1px solid var(--line)!important;border-radius:12px!important;
  padding:4px!important;margin-bottom:24px!important;
}
.st-key-auth_card_streamlit .stTabs [data-baseweb="tab"]{
  flex:1;border-radius:9px!important;background:transparent!important;color:var(--ink-3)!important;
  padding:8px!important;min-height:36px!important;justify-content:center!important;
}
.st-key-auth_card_streamlit .stTabs [data-baseweb="tab"] *,
.st-key-auth_card_streamlit .stTabs [data-baseweb="tab"] p{
  color:inherit!important;
  -webkit-text-fill-color:inherit!important;
  font-family:var(--ui,'Inter','Be Vietnam Pro',system-ui,sans-serif)!important;
  font-size:13px!important;
  font-weight:700!important;
}
.st-key-auth_card_streamlit .stTabs [data-baseweb="tab"][aria-selected="true"]{
  background:var(--surface)!important;color:var(--teal-strong)!important;box-shadow:var(--shadow-sm)!important;
}
.st-key-auth_card_streamlit .stTabs [data-baseweb="tab-highlight"]{display:none!important}
.st-key-auth_card_streamlit [data-testid="stVerticalBlock"]{gap:.55rem}
.st-key-auth_card_streamlit .stSelectbox,
.st-key-auth_card_streamlit .stTextInput{margin-bottom:.25rem}
.st-key-auth_card_streamlit .stButton>button{width:100%}
.st-key-auth_card_streamlit .stSelectbox label,
.st-key-auth_card_streamlit .stTextInput label,
.st-key-auth_card_streamlit [data-testid="stWidgetLabel"],
.st-key-auth_card_streamlit [data-testid="stWidgetLabel"] *{
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
  font-family:var(--ui,'Inter','Be Vietnam Pro',system-ui,sans-serif)!important;
  font-size:12px!important;
  font-weight:700!important;
}
.st-key-auth_card_streamlit .stTextInput div[data-baseweb="input"],
.st-key-auth_card_streamlit .stTextInput div[data-baseweb="base-input"],
.st-key-auth_card_streamlit .stSelectbox div[data-baseweb="select"]>div{
  height:46px!important;
  min-height:46px!important;
  display:flex!important;
  align-items:center!important;
  background:var(--surface)!important;
  border:1px solid var(--line)!important;
  border-radius:10px!important;
  box-shadow:inset 0 1px 0 rgba(15,26,38,.03)!important;
}
.st-key-auth_card_streamlit .stTextInput div[data-baseweb="input"] div[data-baseweb="base-input"]{
  height:auto!important;
  min-height:44px!important;
  flex:1 1 auto!important;
  min-width:0!important;
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
}
.st-key-auth_card_streamlit .stTextInput div[data-baseweb="input"]:focus-within,
.st-key-auth_card_streamlit .stTextInput div[data-baseweb="base-input"]:focus-within{
  background:var(--surface)!important;
  border-color:#b7c9e3!important;
  box-shadow:0 0 0 3px var(--teal-50)!important;
}
.st-key-auth_card_streamlit .stTextInput div[data-baseweb="input"] div[data-baseweb="base-input"]:focus-within{
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
}
.st-key-auth_card_streamlit .stTextInput div[data-baseweb="input"] *,
.st-key-auth_card_streamlit .stTextInput div[data-baseweb="base-input"] *{
  color:var(--ink)!important;
  -webkit-text-fill-color:var(--ink)!important;
}
.st-key-auth_card_streamlit .stTextInput input,
.st-key-auth_card_streamlit .stTextArea textarea,
.st-key-auth_card_streamlit .stSelectbox div[data-baseweb="select"] *,
.st-key-auth_card_streamlit .stRadio label,
.st-key-auth_card_streamlit .stRadio label *{
  color:var(--ink)!important;
  -webkit-text-fill-color:var(--ink)!important;
  font-family:var(--ui,'Inter','Be Vietnam Pro',system-ui,sans-serif)!important;
  font-size:14px!important;
  font-weight:500!important;
}
.st-key-auth_card_streamlit .stTextInput input{
  height:44px!important;
  line-height:44px!important;
  padding:0 14px!important;
  background:transparent!important;
}
.st-key-auth_card_streamlit .stTextInput button{
  width:36px!important;
  min-width:36px!important;
  height:36px!important;
  min-height:36px!important;
  margin-right:4px!important;
  padding:0!important;
  border:0!important;
  border-radius:9px!important;
  background:transparent!important;
  box-shadow:none!important;
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
}
.st-key-auth_card_streamlit .stTextInput button:hover{
  background:var(--surface-2)!important;
  transform:none!important;
}
.st-key-auth_card_streamlit .stTextInput input::placeholder{
  color:var(--ink-3)!important;
  -webkit-text-fill-color:var(--ink-3)!important;
}
.st-key-auth_card_streamlit .stButton>button,
.st-key-auth_card_streamlit .stFormSubmitButton>button{
  min-height:48px!important;
  border-radius:11px!important;
  font-family:var(--ui,'Inter','Be Vietnam Pro',system-ui,sans-serif)!important;
  font-size:14px!important;
  font-weight:700!important;
}
.st-key-auth_card_streamlit .stButton>button:not([kind="primary"]),
.st-key-auth_card_streamlit button[data-testid="stBaseButton-secondary"]{
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
}
.st-key-auth_card_streamlit .stButton>button:not([kind="primary"]) *,
.st-key-auth_card_streamlit [data-testid="stBaseButton-secondary"] p,
.st-key-auth_card_streamlit [data-testid="stBaseButton-secondary"] span,
.st-key-auth_card_streamlit button[data-testid="stBaseButton-secondary"] *{
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
}
.st-key-auth_card_streamlit .stButton>button[kind="primary"],
.st-key-auth_card_streamlit button[data-testid="stBaseButton-primary"],
.st-key-auth_card_streamlit [data-testid="stBaseButton-primary"] p,
.st-key-auth_card_streamlit [data-testid="stBaseButton-primary"] span,
.st-key-auth_card_streamlit button[data-testid="stBaseButton-primary"] *{
  color:#fff!important;
  -webkit-text-fill-color:#fff!important;
}
.st-key-auth_forgot_link button{
  min-height:22px!important;
  height:22px!important;
  width:auto!important;
  margin:7px auto 0!important;
  padding:0!important;
  display:flex!important;
  justify-content:center!important;
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
  color:var(--ink-3)!important;
  -webkit-text-fill-color:var(--ink-3)!important;
  font-size:10.5px!important;
  font-weight:500!important;
}
.st-key-auth_forgot_link button p,
.st-key-auth_forgot_link button span,
.st-key-auth_forgot_link button *{
  color:inherit!important;
  -webkit-text-fill-color:inherit!important;
}
.st-key-auth_forgot_link button:hover{
  transform:none!important;
  color:var(--teal)!important;
  -webkit-text-fill-color:var(--teal)!important;
}
.auth-demo-strip{
  margin-top:17px;
  border-top:1px dashed var(--line);
  padding-top:12px;
}
.auth-demo-strip .dt{
  font-size:10px;
  font-weight:700;
  letter-spacing:.4px;
  text-transform:uppercase;
  color:var(--ink-3)!important;
  text-align:center;
  margin-bottom:10px;
}
.st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_favorite),
.st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_admin_panel_settings){
  gap:7px!important;
  justify-content:center!important;
}
.st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_favorite){
  margin-top:7px!important;
}
.st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_admin_panel_settings){
  margin-top:5px!important;
}
.st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_favorite) > div[data-testid="stColumn"],
.st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_admin_panel_settings) > div[data-testid="stColumn"]{
  flex:0 0 auto!important;
  width:auto!important;
  min-width:max-content!important;
}
.st-key-auth_demo_role_favorite,
.st-key-auth_demo_role_medical_services,
.st-key-auth_demo_role_construction,
.st-key-auth_demo_role_science,
.st-key-auth_demo_role_admin_panel_settings{
  overflow:visible!important;
}
.st-key-auth_card_streamlit .st-key-auth_demo_role_favorite .stButton,
.st-key-auth_card_streamlit .st-key-auth_demo_role_medical_services .stButton,
.st-key-auth_card_streamlit .st-key-auth_demo_role_construction .stButton,
.st-key-auth_card_streamlit .st-key-auth_demo_role_science .stButton,
.st-key-auth_card_streamlit .st-key-auth_demo_role_admin_panel_settings .stButton{
  width:max-content!important;
  max-width:none!important;
  overflow:visible!important;
}
.st-key-auth_card_streamlit .st-key-auth_demo_role_favorite .stButton>button,
.st-key-auth_card_streamlit .st-key-auth_demo_role_medical_services .stButton>button,
.st-key-auth_card_streamlit .st-key-auth_demo_role_construction .stButton>button,
.st-key-auth_card_streamlit .st-key-auth_demo_role_science .stButton>button,
.st-key-auth_card_streamlit .st-key-auth_demo_role_admin_panel_settings .stButton>button{
  min-height:26px!important;
  height:26px!important;
  width:auto!important;
  min-width:0!important;
  border-radius:999px!important;
  padding:0 10px!important;
  font-family:var(--ui,'Inter','Be Vietnam Pro',system-ui,sans-serif)!important;
  font-size:10.5px!important;
  font-weight:600!important;
  background:var(--surface-2)!important;
  border:1px solid var(--line)!important;
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
  box-shadow:none!important;
  white-space:nowrap!important;
  overflow:visible!important;
  text-overflow:clip!important;
  gap:5px!important;
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  line-height:1!important;
}
.st-key-auth_card_streamlit .st-key-auth_demo_role_favorite .stButton>button{
  min-width:0!important;
}
.st-key-auth_card_streamlit .st-key-auth_demo_role_favorite .stButton>button *,
.st-key-auth_card_streamlit .st-key-auth_demo_role_medical_services .stButton>button *,
.st-key-auth_card_streamlit .st-key-auth_demo_role_construction .stButton>button *,
.st-key-auth_card_streamlit .st-key-auth_demo_role_science .stButton>button *,
.st-key-auth_card_streamlit .st-key-auth_demo_role_admin_panel_settings .stButton>button *{
  color:inherit!important;
  -webkit-text-fill-color:inherit!important;
  white-space:nowrap!important;
}
.st-key-auth_card_streamlit .st-key-auth_demo_role_favorite .stButton>button [data-testid="stIconMaterial"],
.st-key-auth_card_streamlit .st-key-auth_demo_role_medical_services .stButton>button [data-testid="stIconMaterial"],
.st-key-auth_card_streamlit .st-key-auth_demo_role_construction .stButton>button [data-testid="stIconMaterial"],
.st-key-auth_card_streamlit .st-key-auth_demo_role_science .stButton>button [data-testid="stIconMaterial"],
.st-key-auth_card_streamlit .st-key-auth_demo_role_admin_panel_settings .stButton>button [data-testid="stIconMaterial"]{
  width:10px!important;
  min-width:10px!important;
  font-size:10px!important;
}
.st-key-auth_card_streamlit .st-key-auth_demo_role_favorite .stButton>button:hover,
.st-key-auth_card_streamlit .st-key-auth_demo_role_medical_services .stButton>button:hover,
.st-key-auth_card_streamlit .st-key-auth_demo_role_construction .stButton>button:hover,
.st-key-auth_card_streamlit .st-key-auth_demo_role_science .stButton>button:hover,
.st-key-auth_card_streamlit .st-key-auth_demo_role_admin_panel_settings .stButton>button:hover{
  border-color:var(--teal)!important;
  color:var(--teal)!important;
  -webkit-text-fill-color:var(--teal)!important;
}

/* ============================================================ TOP BAR */
.topbar{
  position:sticky;top:0;z-index:40;
  display:flex;align-items:center;gap:14px;
  padding:10px clamp(24px,3vw,30px);
  margin:0 calc(50% - 50vw)!important;
  width:100vw!important;
  max-width:100vw!important;
  background:var(--glass);
  backdrop-filter:saturate(160%) blur(14px);
  -webkit-backdrop-filter:saturate(160%) blur(14px);
  border-bottom:1px solid var(--line);
}
.brand{display:flex;align-items:center;gap:11px;min-width:0}
.brand-mark{
  width:40px;height:40px;border-radius:12px;flex:none;
  display:grid;place-items:center;color:#fff;
  background:linear-gradient(145deg,var(--teal),var(--teal-strong));
  box-shadow:0 6px 16px var(--teal-50);
}
.brand-mark .icon{width:23px!important;height:23px!important;stroke-width:2!important}
.brand-txt{display:flex;flex-direction:column;line-height:1.1;min-width:0}
.brand-name{font-family:var(--display);font-weight:600;font-size:20px;letter-spacing:.1px;color:var(--ink)!important}
.brand-name b{color:var(--teal)}
.brand-sub{font-size:11px;color:var(--ink-3)!important;letter-spacing:.3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.spacer{flex:1}

.topbtn{
  height:38px;min-width:38px;padding:0 12px;border-radius:11px;
  display:inline-flex;align-items:center;justify-content:center;gap:8px;
  background:var(--surface);border:1px solid var(--line);color:var(--ink-2)!important;
  text-decoration:none!important;font-size:13px;font-weight:600;transition:.18s;
}
.topbtn:hover{border-color:var(--teal);color:var(--teal)!important;transform:translateY(-1px)}
.topbtn .icon{width:17px;height:17px}
.top-logout:hover{border-color:var(--danger);color:var(--danger)!important}
.rolebadge{
  display:inline-flex;align-items:center;gap:6px;
  padding:4px 10px;border-radius:999px;font-size:11.5px;font-weight:600;
  border:1px solid transparent;white-space:nowrap;
}
.rolebadge .icon{width:13px;height:13px}
.rb-doctor{background:var(--teal-50);color:var(--teal-strong)!important;border-color:var(--teal-50)}
.rb-ktv{background:rgba(2,132,199,.12);color:#0284c7!important;border-color:rgba(2,132,199,.18)}
.rb-ncv{background:var(--ai-50);color:var(--ai)!important;border-color:var(--ai-50)}
.rb-qtv{background:var(--warn-50);color:var(--warn)!important;border-color:var(--warn-50)}
.rb-patient{background:rgba(22,163,74,.12);color:#16a34a!important;border-color:rgba(22,163,74,.18)}

.userchip{display:flex;align-items:center;gap:10px}
.avatar{
  width:36px;height:36px;border-radius:50%;flex:none;display:grid;place-items:center;
  font-weight:700;font-size:13px;color:#fff;background:var(--teal);
}
.userchip .meta{display:flex;flex-direction:column;line-height:1.15}
.userchip .meta .nm{font-size:13.5px;font-weight:600;color:var(--ink)!important}
.userchip .meta .rl{font-size:11px;color:var(--ink-3)!important}

/* ============================================================ SIDEBAR NAV */
.side-section{font-size:10.5px;font-weight:700;letter-spacing:.7px;text-transform:uppercase;color:var(--ink-3);margin:6px 10px 8px}
.navitem{
  display:flex;align-items:center;gap:11px;width:100%;text-align:left;
  border:none;background:transparent;color:var(--ink-2);
  padding:10px 11px;border-radius:11px;font-size:13.5px;font-weight:500;cursor:pointer;
  margin-bottom:2px;transition:.15s;position:relative;
}
.navitem:hover{background:var(--surface-2);color:var(--ink)}
.navitem.on{background:var(--teal-12);color:var(--teal-strong);font-weight:600}
.navitem.on::before{content:"";position:absolute;left:-12px;top:50%;transform:translateY(-50%);width:3px;height:20px;border-radius:3px;background:var(--teal)}

.side-card{margin-top:16px;background:var(--surface-2);border:1px solid var(--line);border-radius:var(--r);padding:13px}
.side-card .h{font-size:12px;font-weight:600;display:flex;align-items:center;gap:7px;margin-bottom:9px}
.side-card .h .icon{width:14px;height:14px;color:var(--teal)}
.side-card .kv{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:5px 0;font-size:12.5px;color:var(--ink-2)}
.side-card .kv b{color:var(--ink);font-family:var(--mono);font-size:12px}

[data-testid="stSidebar"]{
  background:color-mix(in srgb,var(--bg) 88%,var(--surface) 12%)!important;
  border-right:1px solid var(--line)!important;
  visibility:visible!important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
  padding-top:18px!important;
}
[data-testid="stSidebar"] .stButton>button{
  justify-content:flex-start!important;
  min-height:38px!important;
  border-radius:11px!important;
  background:transparent!important;
  border-color:transparent!important;
  color:var(--ink-2)!important;
  box-shadow:none!important;
}
[data-testid="stSidebar"] .stButton>button[kind="primary"],
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]{
  background:var(--teal-12)!important;
  color:var(--teal-strong)!important;
  border-color:transparent!important;
  box-shadow:none!important;
}
[data-testid="stSidebar"] .stButton>button:hover{
  background:var(--surface-2)!important;
  color:var(--teal-strong)!important;
  transform:none!important;
}
.st-key-inline_active_tab_widget{
  margin:12px clamp(14px,3vw,30px) 18px!important;
  padding:10px 12px!important;
  background:var(--glass)!important;
  border:1px solid var(--line)!important;
  border-radius:14px!important;
  backdrop-filter:saturate(160%) blur(14px)!important;
  -webkit-backdrop-filter:saturate(160%) blur(14px)!important;
  box-shadow:var(--shadow-sm)!important;
}
.st-key-inline_active_tab_widget [data-testid="stSegmentedControl"]{
  width:100%!important;
}
.st-key-inline_active_tab_widget [role="radiogroup"],
.st-key-inline_active_tab_widget [role="group"]{
  display:flex!important;
  gap:7px!important;
  overflow-x:auto!important;
  padding:2px!important;
}
.st-key-inline_active_tab_widget button{
  white-space:nowrap!important;
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
}
.st-key-inline_active_tab_widget button[aria-checked="true"],
.st-key-inline_active_tab_widget button[aria-pressed="true"],
.st-key-inline_active_tab_widget button[kind="segmented_controlActive"]{
  color:#fff!important;
  -webkit-text-fill-color:#fff!important;
}
.st-key-auth_card_streamlit .stRadio [role="radiogroup"]{
  display:grid!important;
  grid-template-columns:1fr 1fr;
  gap:10px!important;
  margin-top:8px!important;
}
.st-key-auth_card_streamlit .stRadio > label,
.st-key-auth_card_streamlit .stRadio [data-testid="stWidgetLabel"]{
  min-height:42px!important;
  display:flex!important;
  align-items:center!important;
  margin:0 0 6px!important;
  padding:0 12px!important;
  background:var(--surface-2)!important;
  border:1px solid var(--line)!important;
  border-radius:10px!important;
  color:var(--ink)!important;
  -webkit-text-fill-color:var(--ink)!important;
  font-size:13px!important;
  font-weight:500!important;
}
.st-key-auth_card_streamlit .stRadio [role="radiogroup"] label{
  min-height:54px!important;
  display:flex!important;
  align-items:center!important;
  background:var(--surface-2)!important;
  border:1px solid var(--line)!important;
  border-radius:11px!important;
  padding:10px 12px!important;
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
  font-size:14px!important;
  font-weight:600!important;
}
.st-key-auth_card_streamlit .stRadio [role="radiogroup"] label:has(input:checked),
.st-key-auth_card_streamlit .stRadio [role="radiogroup"] label:has([aria-checked="true"]){
  border-color:var(--teal)!important;
  background:var(--teal-12)!important;
  color:var(--teal-strong)!important;
  -webkit-text-fill-color:var(--teal-strong)!important;
  box-shadow:0 0 0 1px var(--teal)!important;
}
.st-key-auth_card_streamlit .stRadio [role="radiogroup"] label:has(input:checked) *,
.st-key-auth_card_streamlit .stRadio [role="radiogroup"] label:has([aria-checked="true"]) *{
  color:var(--teal-strong)!important;
  -webkit-text-fill-color:var(--teal-strong)!important;
}

@media (max-width:980px){
  .auth-wrap{grid-template-columns:1fr}
  .auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"],
  .stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit){
    display:grid!important;
    grid-template-columns:1fr!important;
    gap:18px!important;
    padding:42px 16px 24px!important;
  }
  .auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
  .stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit) > div[data-testid="stColumn"]{
    grid-column:1!important;
    width:100%!important;
  }
  .auth-hero{min-height:auto;padding:8px 0 4px;gap:12px}
  .auth-hero h1,
  .auth-hero .auth-hero-title{font-size:clamp(36px,9.5vw,50px)!important;line-height:1.05!important}
  .pose-card{position:relative;right:auto;bottom:auto;width:200px;align-self:center;margin-top:6px}
  .auth-panel{padding-top:0}
  .st-key-auth_card_streamlit{padding:24px 18px!important}
}
.stApp:has(.auth-shell-anchor) .auth-hero-title,
.auth-hero-title{
  display:block!important;
  margin:0!important;
  max-width:30ch!important;
  font-family:var(--display,'Fraunces',Georgia,serif)!important;
  font-size:clamp(48px,4vw,58px)!important;
  line-height:1.04!important;
  font-weight:600!important;
  letter-spacing:0!important;
  color:var(--ink,#111827)!important;
  text-wrap:wrap!important;
  word-break:keep-all!important;
  overflow-wrap:normal!important;
  hyphens:none!important;
  font-kerning:normal!important;
}
.stApp:has(.auth-shell-anchor) .brand-name,
.stApp:has(.auth-shell-anchor) .auth-card-title h2,
.stApp:has(.auth-shell-anchor) .auth-card-head h2{
  font-family:var(--display,'Fraunces',Georgia,serif)!important;
  font-weight:600!important;
  letter-spacing:0!important;
}
.stApp:has(.auth-shell-anchor) .brand-sub,
.stApp:has(.auth-shell-anchor) .auth-card-title p,
.stApp:has(.auth-shell-anchor) .auth-hero p.lede,
.stApp:has(.auth-shell-anchor) .eyebrow,
.stApp:has(.auth-shell-anchor) label,
.stApp:has(.auth-shell-anchor) input,
.stApp:has(.auth-shell-anchor) button{
  font-family:var(--ui,'Inter','Be Vietnam Pro',system-ui,sans-serif)!important;
}
.stApp:has(.auth-shell-anchor) .auth-hero-title em,
.auth-hero-title em{
  font-family:inherit!important;
  font-size:inherit!important;
  line-height:inherit!important;
  font-weight:inherit!important;
  font-style:italic!important;
  color:var(--teal,#1d6fe8)!important;
  white-space:normal!important;
}
.stApp:has(.auth-shell-anchor) .auth-hero-title span,
.auth-hero-title span{
  font-family:inherit!important;
  font-size:inherit!important;
  line-height:inherit!important;
  font-weight:inherit!important;
  color:inherit!important;
  white-space:nowrap!important;
}
.stApp:has(.auth-shell-anchor) .auth-hero-title .auth-word,
.auth-hero-title .auth-word{
  display:inline-block!important;
  font-family:inherit!important;
  font-size:inherit!important;
  line-height:inherit!important;
  font-weight:inherit!important;
  letter-spacing:0!important;
  word-break:keep-all!important;
  overflow-wrap:normal!important;
  hyphens:none!important;
  white-space:nowrap!important;
}
@media (max-width:640px){
  .stApp:has(.auth-shell-anchor) .auth-hero-title,
  .auth-hero-title{font-size:clamp(38px,10.5vw,46px)!important;line-height:1.05!important}
}
@media (max-width:760px){
  .stApp:has(.auth-shell-anchor) [data-testid="stAppViewContainer"]>.main .block-container{
    padding:0!important;
    width:100%!important;
    max-width:100%!important;
    overflow-x:hidden!important;
  }
  .topbar{
    min-height:58px!important;
    padding:9px 54px 9px 14px!important;
    gap:9px!important;
    overflow:hidden!important;
  }
  .brand{gap:9px!important;max-width:100%!important}
  .brand-mark{
    width:34px!important;
    height:34px!important;
    border-radius:10px!important;
  }
  .brand-mark .icon{width:20px!important;height:20px!important}
  .brand-name{
    font-size:17px!important;
    line-height:1.05!important;
    white-space:nowrap!important;
    overflow:hidden!important;
    text-overflow:ellipsis!important;
  }
  .brand-sub{
    max-width:calc(100vw - 112px)!important;
    font-size:11px!important;
    line-height:1.18!important;
    white-space:nowrap!important;
    overflow:hidden!important;
    text-overflow:ellipsis!important;
  }
  .st-key-auth_theme_icon_button{
    top:10px!important;
    right:12px!important;
    width:36px!important;
    height:36px!important;
  }
  .st-key-auth_theme_icon_button .stButton>button,
  .st-key-auth_theme_icon_button button{
    width:36px!important;
    height:36px!important;
    min-height:36px!important;
    border-radius:10px!important;
    font-size:18px!important;
  }
  .auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"],
  .stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit){
    display:flex!important;
    flex-direction:column!important;
    align-items:center!important;
    gap:0!important;
    width:100%!important;
    min-height:calc(100svh - 58px)!important;
    padding:36px 14px 24px!important;
    overflow:hidden!important;
  }
  .auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
  .stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit) > div[data-testid="stColumn"]{
    width:100%!important;
    min-width:0!important;
    max-width:430px!important;
    flex:0 0 auto!important;
  }
  .auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child,
  .stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit) > div[data-testid="stColumn"]:first-child{
    display:none!important;
  }
  .auth-layout-row-anchor + div > [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child,
  .stApp:has(.auth-shell-anchor) [data-testid="stHorizontalBlock"]:has(.auth-hero):has(.st-key-auth_card_streamlit) > div[data-testid="stColumn"]:last-child{
    display:block!important;
    max-width:430px!important;
    margin:0 auto!important;
  }
  .auth-hero,
  .auth-hero .eyebrow,
  .auth-hero .auth-hero-title,
  .auth-hero p.lede,
  .hero-stats,
  .pose-card{
    display:none!important;
    min-height:0!important;
  }
  .auth-card-streamlit,
  .st-key-auth_card_streamlit{
    width:100%!important;
    max-width:430px!important;
    margin:0 auto!important;
    align-self:center!important;
  }
  .st-key-auth_card_streamlit{
    border-radius:18px!important;
    padding:26px 18px 22px!important;
  }
  .auth-card-title h2{
    font-size:22px!important;
    line-height:1.14!important;
    margin-bottom:8px!important;
  }
  .auth-card-title p{
    font-size:13px!important;
    line-height:1.45!important;
    margin-bottom:18px!important;
  }
  .st-key-auth_card_streamlit .stTabs [data-baseweb="tab-list"]{
    margin-bottom:18px!important;
  }
  .st-key-auth_card_streamlit .stTabs [data-baseweb="tab"]{
    min-height:34px!important;
    padding:7px!important;
  }
  .st-key-auth_card_streamlit .stTextInput div[data-baseweb="input"],
  .st-key-auth_card_streamlit .stTextInput div[data-baseweb="base-input"],
  .st-key-auth_card_streamlit .stSelectbox div[data-baseweb="select"]>div{
    height:42px!important;
    min-height:42px!important;
  }
  .st-key-auth_card_streamlit .stTextInput input{
    height:40px!important;
    line-height:40px!important;
    font-size:13px!important;
  }
  .st-key-auth_card_streamlit .stButton>button,
  .st-key-auth_card_streamlit .stFormSubmitButton>button{
    min-height:44px!important;
  }
  .st-key-auth_forgot_link .stButton>button,
  .st-key-auth_forgot_link button{
    width:auto!important;
    min-height:22px!important;
    margin:7px auto 0!important;
    padding:0!important;
    background:transparent!important;
    border:0!important;
    box-shadow:none!important;
    white-space:normal!important;
  }
  .auth-demo-strip{
    margin-top:15px!important;
    padding-top:11px!important;
  }
  .st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_favorite),
  .st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_admin_panel_settings){
    display:flex!important;
    flex-wrap:wrap!important;
    justify-content:center!important;
    gap:6px!important;
  }
  .st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_favorite) > div[data-testid="stColumn"],
  .st-key-auth_card_streamlit [data-testid="stHorizontalBlock"]:has(.st-key-auth_demo_role_admin_panel_settings) > div[data-testid="stColumn"]{
    width:auto!important;
    flex:0 0 auto!important;
    min-width:max-content!important;
  }
}
"""

def inject_auth_nav_css():
    """Inject CSS cho auth screen và navigation."""
    st.markdown("<style>" + _AUTH_NAV_CSS + "</style>", unsafe_allow_html=True)
