(function () {
  const MSG_READY = "streamlit:componentReady";
  const MSG_VALUE = "streamlit:setComponentValue";
  const MSG_HEIGHT = "streamlit:setFrameHeight";
  const MSG_RENDER = "streamlit:render";
  const STORAGE_KEY = "rehab-ai-shell";

  const iconSprite = `
  <svg xmlns="http://www.w3.org/2000/svg" style="display:none">
    <symbol id="i-pulse" viewBox="0 0 24 24"><path d="M3 12h4l2-7 4 14 3-7h5"/></symbol>
    <symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></symbol>
    <symbol id="i-close" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></symbol>
    <symbol id="i-logout" viewBox="0 0 24 24"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 16l4-4-4-4M14 12H3"/></symbol>
    <symbol id="i-moon" viewBox="0 0 24 24"><path d="M21 12.8A8.5 8.5 0 1 1 11.2 3a6.5 6.5 0 0 0 9.8 9.8Z"/></symbol>
    <symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></symbol>
    <symbol id="i-heart" viewBox="0 0 24 24"><path d="M20.8 5.6a5.1 5.1 0 0 0-7.2 0L12 7.2l-1.6-1.6a5.1 5.1 0 1 0-7.2 7.2L12 21l8.8-8.2a5.1 5.1 0 0 0 0-7.2Z"/></symbol>
    <symbol id="i-stetho" viewBox="0 0 24 24"><path d="M6 3v5a4 4 0 0 0 8 0V3M4 3h4M12 3h4M10 14v2a5 5 0 0 0 10 0v-3"/><circle cx="20" cy="11" r="2"/></symbol>
    <symbol id="i-tools" viewBox="0 0 24 24"><path d="m14.7 6.3 3-3 3 3-3 3M13 8l-9 9 3 3 9-9M5 6l4 4"/></symbol>
    <symbol id="i-ktv" viewBox="0 0 24 24"><path d="m14.7 6.3 3-3 3 3-3 3M13 8l-9 9 3 3 9-9M5 6l4 4"/></symbol>
    <symbol id="i-micro" viewBox="0 0 24 24"><path d="M9 3h6M10 3v6L5 18a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 18l-5-9V3"/><path d="M7.5 14h9"/></symbol>
    <symbol id="i-cog" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2 3.4-.2-.1a1.7 1.7 0 0 0-2 .2l-.6.4a1.7 1.7 0 0 0-1 1.6V23h-4v-.5a1.7 1.7 0 0 0-1-1.6l-.6-.4a1.7 1.7 0 0 0-2-.2l-.2.1-2-3.4.1-.1A1.7 1.7 0 0 0 4.6 15l-.2-.7A1.7 1.7 0 0 0 3 13H2v-4h1a1.7 1.7 0 0 0 1.4-1.3l.2-.7a1.7 1.7 0 0 0-.3-1.9l-.1-.1 2-3.4.2.1a1.7 1.7 0 0 0 2-.2l.6-.4A1.7 1.7 0 0 0 10 0h4v.5a1.7 1.7 0 0 0 1 1.6l.6.4a1.7 1.7 0 0 0 2 .2l.2-.1 2 3.4-.1.1a1.7 1.7 0 0 0-.3 1.9l.2.7A1.7 1.7 0 0 0 21 9h1v4h-1a1.7 1.7 0 0 0-1.4 1.3Z"/></symbol>
    <symbol id="i-db" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="7" ry="3"/><path d="M5 5v14c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/></symbol>
    <symbol id="i-users" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2M9.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/></symbol>
    <symbol id="i-bars" viewBox="0 0 24 24"><path d="M4 19V5M4 19h16M8 16V9M13 16V4M18 16v-6"/></symbol>
    <symbol id="i-flask" viewBox="0 0 24 24"><path d="M9 3h6M10 3v6L5 18a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 18l-5-9V3"/><path d="M7.5 14h9"/></symbol>
    <symbol id="i-video" viewBox="0 0 24 24"><path d="M4 6h11a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4zM17 10l4-3v10l-4-3"/></symbol>
    <symbol id="i-bell" viewBox="0 0 24 24"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></symbol>
    <symbol id="i-doc" viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6zM14 3v4h4"/><path d="M9 12h6M9 16h6M9 8h3"/></symbol>
    <symbol id="i-mail" viewBox="0 0 24 24"><path d="M4 6h16v12H4z"/><path d="m4 7 8 6 8-6"/></symbol>
    <symbol id="i-lock" viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></symbol>
    <symbol id="i-eye" viewBox="0 0 24 24"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></symbol>
    <symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></symbol>
    <symbol id="i-log" viewBox="0 0 24 24"><path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"/></symbol>
    <symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></symbol>
    <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
    <symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/></symbol>
    <symbol id="i-dumbbell" viewBox="0 0 24 24"><path d="M6 7v10M18 7v10M3 9v6M21 9v6M6 12h12"/></symbol>
    <symbol id="i-spark" viewBox="0 0 24 24"><path d="M12 2l1.7 6.3L20 10l-6.3 1.7L12 18l-1.7-6.3L4 10l6.3-1.7Z"/></symbol>
    <symbol id="i-check" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></symbol>
    <symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></symbol>
    <symbol id="i-bone" viewBox="0 0 24 24"><path d="M7 7a3 3 0 1 1 4-4 3 3 0 0 1 4 4l2 2a3 3 0 1 1-4 4l-2-2-4 4 2 2a3 3 0 1 1-4 4 3 3 0 0 1-4-4 3 3 0 0 1 4-4l4-4Z"/></symbol>
    <symbol id="i-broom" viewBox="0 0 24 24"><path d="m14 4 6 6M12 6l6 6-7 7H5l-2-2 7-7Z"/><path d="M5 19v2M9 19v2M13 19v2"/></symbol>
    <symbol id="i-chuc-nang" viewBox="0 0 24 24"><path d="M12 3v18M5 8h14M7 16h10"/><circle cx="12" cy="12" r="9"/></symbol>
    <symbol id="i-sai" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></symbol>
  </svg>`;

  const css = `
  :root {
    --rehab-primary:#0F172A;
    --rehab-secondary:#475569;
    --rehab-blue:#1F6FE0;
    --rehab-blue-strong:#1657BC;
    --rehab-accent:#0284C7;
    --rehab-success:#059669;
    --rehab-warning:#D97706;
    --rehab-danger:#DC2626;
    --rehab-bg:#E8EDF5;
    --rehab-bg-soft:#F8FAFC;
    --rehab-card:#FFFFFF;
    --rehab-surface-2:#F4F7FC;
    --rehab-surface-3:#EDF2FA;
    --rehab-line:#DFE6F1;
    --rehab-muted:#64748B;
    --rehab-shadow:0 22px 55px rgba(15,23,42,.13);
    --rehab-shadow-sm:0 4px 12px rgba(15,23,42,.08);
    --rehab-ui:Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --rehab-display:"Fraunces", Georgia, "Times New Roman", serif;
    --rehab-mono:"IBM Plex Mono", "JetBrains Mono", "Fira Code", monospace;
    --rehab-r:8px;
    --rehab-r-lg:20px;
    --rehab-topbar-h:72px;
    --rehab-content-top:72px;
    --rehab-drawer-w:336px;
    --ag-neutral-bg:#F8FAFC;
    --ag-card-bg:#FFFFFF;
    --ag-terminal-bg:#0B0F19;
    --ag-accent:#0284C7;
    --ag-success:#059669;
    --ag-warning:#D97706;
    --ag-danger:#DC2626;
  }
  html[data-rehab-theme="dark"] {
    --rehab-primary:#E5EDF7;
    --rehab-secondary:#A9B8CB;
    --rehab-blue:#5B9BFF;
    --rehab-blue-strong:#8BB6FF;
    --rehab-bg:#0A1119;
    --rehab-bg-soft:#111A26;
    --rehab-card:#101A27;
    --rehab-surface-2:#152130;
    --rehab-surface-3:#1A2839;
    --rehab-line:#1F2C3B;
    --rehab-muted:#7C8B9B;
    --rehab-shadow:0 22px 50px rgba(0,0,0,.34);
    --rehab-shadow-sm:0 2px 8px rgba(0,0,0,.24);
    --ag-neutral-bg:#0A1119;
    --ag-card-bg:#101A27;
  }
  html[data-rehab-shell] body,
  html[data-rehab-shell] .stApp,
  html[data-rehab-shell] [data-testid="stAppViewContainer"],
  html[data-rehab-shell] [data-testid="stMainViewContainer"] {
    background:
      radial-gradient(60vw 50vh at 8% -8%, rgba(37,110,217,.11), transparent 60%),
      radial-gradient(55vw 50vh at 105% 0%, rgba(124,115,255,.10), transparent 55%),
      var(--rehab-bg) !important;
    color: var(--rehab-primary) !important;
    font-family: var(--rehab-ui) !important;
  }
  html[data-rehab-shell] [data-testid="stHeader"],
  html[data-rehab-shell] [data-testid="stToolbar"],
  html[data-rehab-shell] [data-testid="stDecoration"],
  html[data-rehab-shell] #MainMenu { display:none !important; }
  html[data-rehab-shell] [data-testid="stSidebar"],
  html[data-rehab-shell] [data-testid="stSidebarCollapsedControl"] { display:none !important; }
  html[data-rehab-shell] [data-testid="stAppViewContainer"] > .main .block-container {
    padding-top: calc(var(--rehab-content-top) + 16px) !important;
    max-width: min(1560px, calc(100vw - 80px)) !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    transition:max-width .2s ease, margin .2s ease, padding .2s ease;
  }
  html[data-rehab-shell][data-rehab-drawer-open="true"] [data-testid="stAppViewContainer"] > .main .block-container {
    max-width: min(1560px, calc(100vw - var(--rehab-drawer-w) - 80px)) !important;
    margin-left: calc(var(--rehab-drawer-w) + 40px) !important;
    margin-right: 40px !important;
  }
  html[data-rehab-shell] .rehab-js-content-anchor { height:0 !important; }
  #rehab-react-root {
    position:relative; z-index:5; width:min(1560px, calc(100vw - 80px));
    margin:calc(var(--rehab-content-top) + 16px) auto 24px;
    transition:width .2s ease, margin .2s ease, opacity .16s ease;
  }
  #rehab-react-root:empty { display:none; }
  html[data-rehab-drawer-open="true"] #rehab-react-root {
    width:min(1560px, calc(100vw - var(--rehab-drawer-w) - 80px));
    margin-left:calc(var(--rehab-drawer-w) + 40px);
    margin-right:40px;
  }
  html[data-rehab-mode="auth"] #rehab-react-root { display:none; }
  .rehab-react-shell {
    font-family:var(--rehab-ui); color:var(--rehab-primary);
  }
  .rehab-react-shell * { box-sizing:border-box; letter-spacing:0; }
  .rehab-react-title {
    display:flex; align-items:flex-end; justify-content:space-between; gap:24px; margin:0 0 18px;
  }
  .rehab-react-title h1 {
    margin:0; color:var(--rehab-primary);
    font:700 clamp(28px, 2.3vw, 38px)/1.08 var(--rehab-display);
  }
  .rehab-react-title p { margin:8px 0 0; color:var(--rehab-muted); font-size:14.5px; line-height:1.55; }
  .rehab-react-grid { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:16px; margin:0 0 20px; }
  .rehab-react-card {
    background:var(--rehab-card); border:1px solid var(--rehab-line); border-radius:8px;
    box-shadow:var(--rehab-shadow-sm); padding:16px;
  }
  .rehab-react-metric b { display:block; color:var(--rehab-primary); font:900 26px/1 var(--rehab-mono); }
  .rehab-react-metric span { display:block; color:var(--rehab-secondary); font-weight:800; margin-top:8px; }
  .rehab-react-metric small { display:block; color:var(--rehab-muted); margin-top:6px; font-size:12px; }
  .rehab-react-panel { display:grid; grid-template-columns:minmax(0, 1fr) minmax(260px, .45fr); gap:18px; align-items:start; }
  .rehab-react-card h2, .rehab-react-card h3 {
    margin:0 0 12px; color:var(--rehab-primary); font:900 16px/1.25 var(--rehab-ui) !important;
  }
  .rehab-react-form { display:grid; gap:12px; }
  .rehab-react-field label { display:block; color:var(--rehab-secondary); font:800 12px/1.2 var(--rehab-ui); margin-bottom:7px; }
  .rehab-react-field input,
  .rehab-react-field select,
  .rehab-react-field textarea {
    width:100%; min-height:42px; padding:12px 16px; border-radius:8px;
    border:1px solid var(--rehab-line); background:var(--rehab-bg-soft);
    color:var(--rehab-primary); font:600 14px var(--rehab-ui); outline:0;
  }
  .rehab-react-field textarea { min-height:96px; resize:vertical; }
  .rehab-react-field input:focus,
  .rehab-react-field select:focus,
  .rehab-react-field textarea:focus {
    border-color:var(--rehab-blue); box-shadow:0 0 0 3px rgba(31,111,224,.12);
  }
  .rehab-react-button {
    min-height:44px; border:0; border-radius:8px; cursor:pointer;
    background:linear-gradient(145deg, var(--rehab-blue), var(--rehab-blue-strong)); color:#fff;
    font:900 13.5px var(--rehab-ui); box-shadow:0 8px 20px rgba(31,111,224,.22);
  }
  .rehab-react-button.secondary {
    background:var(--rehab-bg-soft); color:var(--rehab-blue-strong); border:1px solid var(--rehab-line); box-shadow:none;
  }
  .rehab-react-table { width:100%; border-collapse:collapse; overflow:hidden; border-radius:8px; }
  .rehab-react-table th, .rehab-react-table td {
    border-bottom:1px solid var(--rehab-line); padding:11px 12px; text-align:left; font-size:13px;
  }
  .rehab-react-table th { color:var(--rehab-muted); text-transform:uppercase; font-size:11px; font-weight:900; background:var(--rehab-bg-soft); }
  .rehab-react-list { display:grid; gap:10px; }
  .rehab-react-list-item {
    display:flex; justify-content:space-between; gap:12px; padding:12px;
    border:1px solid var(--rehab-line); border-radius:8px; background:var(--rehab-bg-soft);
  }
  .rehab-react-list-item b { color:var(--rehab-primary); }
  .rehab-react-list-item span { color:var(--rehab-muted); font-size:12px; }
  .rehab-react-notice {
    padding:11px 12px; border-radius:8px; margin-bottom:12px; border:1px solid rgba(31,111,224,.22);
    background:rgba(31,111,224,.10); color:var(--rehab-blue-strong); font:800 13px var(--rehab-ui);
  }
  .rehab-react-notice.error {
    border-color:rgba(220,38,38,.25); background:rgba(220,38,38,.10); color:var(--rehab-danger);
  }
  html[data-rehab-shell] h1,
  html[data-rehab-shell] h2,
  html[data-rehab-shell] h3 {
    color: var(--rehab-primary) !important;
    letter-spacing: 0 !important;
  }
  html[data-rehab-shell] h1,
  html[data-rehab-shell] h2 {
    font-family: var(--rehab-display) !important;
    font-weight: 700 !important;
  }
  html[data-rehab-shell] p,
  html[data-rehab-shell] li,
  html[data-rehab-shell] label,
  html[data-rehab-shell] [data-testid="stMarkdownContainer"] {
    font-family: var(--rehab-ui) !important;
  }
  #rehab-ui-sprite { position:absolute; width:0; height:0; overflow:hidden; }
  .rehab-icon { width:18px; height:18px; fill:none; stroke:currentColor; stroke-width:1.7; stroke-linecap:round; stroke-linejoin:round; flex:none; }
  .rehab-topbar {
    position:fixed; z-index:2147482600; top:0; left:0; right:0;
    min-height:var(--rehab-topbar-h);
    display:grid; grid-template-columns:minmax(220px, 330px) minmax(220px, 1fr) minmax(0, auto);
    align-items:center; gap:14px;
    padding:12px clamp(14px, 2.6vw, 28px);
    background:rgba(248,250,252,.92);
    border-bottom:1px solid var(--rehab-line);
    backdrop-filter:saturate(160%) blur(14px);
    -webkit-backdrop-filter:saturate(160%) blur(14px);
  }
  html[data-rehab-theme="dark"] .rehab-topbar { background:rgba(11,17,27,.92); }
  .rehab-brand { display:flex; align-items:center; gap:11px; min-width:0; }
  .rehab-brand-mark {
    width:40px; height:40px; border-radius:12px; display:grid; place-items:center;
    color:#fff; background:linear-gradient(145deg, var(--rehab-blue), var(--rehab-blue-strong));
    box-shadow:0 6px 16px rgba(37,110,217,.30); flex:none;
  }
  .rehab-brand-mark .rehab-icon { width:23px; height:23px; stroke-width:2; }
  .rehab-brand-text { min-width:0; display:flex; flex-direction:column; line-height:1.1; }
  .rehab-brand-name { font-family:var(--rehab-display); font-weight:650; font-size:18px; color:var(--rehab-primary); white-space:nowrap; }
  .rehab-brand-name b { color:var(--rehab-blue); }
  .rehab-brand-sub { font-size:12px; color:var(--rehab-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .rehab-tabs {
    display:flex; align-items:center; justify-content:center; gap:8px;
    overflow-x:auto; overflow-y:hidden; scrollbar-width:none; min-width:0;
  }
  .rehab-tabs::-webkit-scrollbar { display:none; }
  .rehab-tab {
    display:inline-flex; align-items:center; gap:7px; height:38px; padding:0 14px;
    border:0; border-radius:999px; background:transparent; color:var(--rehab-secondary);
    font:600 13.5px/1 var(--rehab-ui); cursor:pointer; white-space:nowrap;
  }
  .rehab-tab:hover { color:var(--rehab-blue-strong); background:rgba(37,110,217,.08); }
  .rehab-tab.is-active { color:var(--rehab-blue-strong); background:rgba(37,110,217,.13); }
  .rehab-tab .rehab-icon { width:16px; height:16px; }
  .rehab-actions {
    display:flex; align-items:center; gap:8px; min-width:0; max-width:min(48vw, 560px);
    justify-content:flex-end; overflow:hidden;
  }
  .rehab-rolebadge {
    display:inline-flex; align-items:center; gap:6px; padding:6px 11px; border-radius:999px;
    border:1px solid rgba(37,110,217,.20); background:rgba(37,110,217,.11);
    color:var(--rehab-blue-strong); font-weight:700; font-size:12.5px; white-space:nowrap;
  }
  .rehab-rolebadge.rb-ncv { background:rgba(99,102,241,.12); border-color:rgba(99,102,241,.22); color:#5B5FEF; }
  .rehab-rolebadge.rb-qtv { background:rgba(217,119,6,.12); border-color:rgba(217,119,6,.22); color:#B76105; }
  .rehab-rolebadge.rb-patient { background:rgba(5,150,105,.12); border-color:rgba(5,150,105,.22); color:var(--rehab-success); }
  html[data-rehab-theme="dark"] .rehab-rolebadge.rb-ncv { color:#A8A5FF; }
  html[data-rehab-theme="dark"] .rehab-rolebadge.rb-qtv { color:#F8B44B; }
  html[data-rehab-theme="dark"] .rehab-rolebadge.rb-patient { color:#5EE1A7; }
  .rehab-userchip { display:flex; align-items:center; gap:10px; min-width:0; max-width:210px; flex:1 1 150px; }
  .rehab-avatar {
    width:36px; height:36px; border-radius:50%; display:grid; place-items:center;
    background:var(--rehab-blue); color:#fff; font-size:13px; font-weight:800; flex:none;
  }
  .rehab-user-meta { min-width:0; max-width:154px; display:flex; flex-direction:column; line-height:1.15; }
  .rehab-user-name { font-size:13.5px; font-weight:800; color:var(--rehab-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .rehab-user-role { font-size:11.5px; color:var(--rehab-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .rehab-icon-btn {
    width:38px; height:38px; border-radius:11px; border:1px solid var(--rehab-line);
    background:var(--rehab-card); color:var(--rehab-secondary); display:grid; place-items:center;
    cursor:pointer; transition:.16s; flex:none;
  }
  .rehab-icon-btn:hover { border-color:var(--rehab-blue); color:var(--rehab-blue); transform:translateY(-1px); }
  .rehab-drawer-fab {
    position:fixed; z-index:2147482565; left:14px; top:calc(var(--rehab-content-top) + 12px);
    width:38px; height:38px; border-radius:12px; border:1px solid var(--rehab-line);
    background:var(--rehab-card); color:var(--rehab-blue-strong);
    display:grid; place-items:center; cursor:pointer; box-shadow:var(--rehab-shadow-sm);
    transition:transform .16s ease, opacity .16s ease, border-color .16s ease;
  }
  .rehab-drawer-fab:hover { transform:translateY(-1px); border-color:var(--rehab-blue); }
  .rehab-drawer-fab.is-hidden { display:none; }
  .rehab-drawer {
    position:fixed; z-index:2147482550; top:var(--rehab-topbar-h); left:0; bottom:0; width:var(--rehab-drawer-w);
    background:rgba(248,250,252,.96); border-right:1px solid var(--rehab-line);
    box-shadow:14px 0 34px rgba(15,23,42,.08); transform:translateX(-104%);
    transition:transform .2s ease; padding:18px 16px 28px; overflow-y:auto;
    font-family:var(--rehab-ui);
  }
  html[data-rehab-theme="dark"] .rehab-drawer { background:rgba(11,17,27,.96); }
  .rehab-drawer.is-open { transform:translateX(0); }
  .rehab-drawer-title { display:flex; align-items:center; gap:8px; font-size:12px; text-transform:uppercase; letter-spacing:.4px; color:var(--rehab-muted); font-weight:900; margin:2px 4px 12px; }
  .rehab-drawer-role { display:flex; align-items:center; gap:10px; padding:12px; border-radius:8px; background:var(--rehab-card); border:1px solid var(--rehab-line); box-shadow:var(--rehab-shadow-sm); margin-bottom:14px; }
  .rehab-drawer-role .rehab-icon { color:var(--rehab-blue-strong); }
  .rehab-drawer-role b { display:block; color:var(--rehab-primary); font-size:13px; line-height:1.25; }
  .rehab-drawer-role span { display:block; color:var(--rehab-muted); font-size:12px; margin-top:2px; }
  .rehab-side-card {
    margin-top:12px; background:var(--rehab-card); border:1px solid var(--rehab-line);
    border-radius:8px; padding:14px; box-shadow:var(--rehab-shadow-sm);
  }
  .rehab-side-card h3 { display:flex; align-items:center; gap:8px; margin:0 0 10px; font-size:13px; font-weight:900; color:var(--rehab-primary); }
  .rehab-side-card p { margin:7px 0; color:var(--rehab-secondary); font-size:12.5px; line-height:1.5; }
  .rehab-side-muted { color:var(--rehab-muted); font-size:12px; line-height:1.45; }
  .rehab-kv { display:flex; justify-content:space-between; gap:12px; padding:5px 0; color:var(--rehab-secondary); font-size:12.5px; }
  .rehab-kv b { color:var(--rehab-primary); font-family:var(--rehab-mono); }
  .rehab-side-metrics { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px; }
  .rehab-side-metric { padding:12px 8px; border-radius:8px; border:1px solid var(--rehab-line); background:var(--rehab-bg-soft); text-align:center; }
  .rehab-side-metric span { display:block; color:var(--rehab-muted); font-size:10px; line-height:1.2; font-weight:900; text-transform:uppercase; }
  .rehab-side-metric b { display:block; margin-top:6px; color:var(--rehab-blue-strong); font:900 22px/1 var(--rehab-mono); }
  .rehab-side-field { margin:12px 0; }
  .rehab-side-field label { display:flex; align-items:center; gap:7px; color:var(--rehab-secondary); font:800 12px/1.2 var(--rehab-ui); margin-bottom:7px; }
  .rehab-side-field input[type="range"] { width:100%; accent-color:var(--rehab-blue); }
  .rehab-side-range-row { display:flex; justify-content:space-between; color:var(--rehab-muted); font:700 11px var(--rehab-mono); margin-top:2px; }
  .rehab-side-select, .rehab-side-input {
    width:100%; min-height:38px; border:1px solid var(--rehab-line); border-radius:8px;
    background:var(--rehab-bg-soft); color:var(--rehab-primary); padding:9px 11px;
    font:700 12.5px var(--rehab-ui); outline:0;
  }
  .rehab-side-select:focus, .rehab-side-input:focus { border-color:var(--rehab-blue); box-shadow:0 0 0 3px rgba(31,111,224,.12); }
  .rehab-side-button {
    width:100%; min-height:40px; border:1px solid var(--rehab-line); border-radius:8px;
    background:linear-gradient(145deg, var(--rehab-blue), var(--rehab-blue-strong)); color:#fff;
    font:900 12.5px var(--rehab-ui); cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px;
  }
  .rehab-side-button.secondary { background:var(--rehab-bg-soft); color:var(--rehab-blue-strong); }
  .rehab-side-result { margin-top:10px; padding:10px; border-radius:8px; border:1px solid var(--rehab-line); background:var(--rehab-bg-soft); color:var(--rehab-secondary); font-size:12px; line-height:1.45; }
  .rehab-side-result b { color:var(--rehab-primary); }
  .rehab-side-divider { border:0; border-top:1px dashed var(--rehab-line); margin:14px 0; }
  .rehab-side-guide { display:grid; gap:9px; }
  .rehab-side-guide-item { padding:10px; border-radius:8px; border:1px solid var(--rehab-line); background:var(--rehab-bg-soft); }
  .rehab-side-guide-item b { display:flex; align-items:center; gap:7px; color:var(--rehab-primary); font-size:12.5px; }
  .rehab-side-guide-item span { display:block; color:var(--rehab-muted); font-size:11.5px; line-height:1.45; margin-top:4px; }
  .rehab-backdrop {
    position:fixed; inset:var(--rehab-topbar-h) 0 0 0; background:rgba(15,23,42,.22);
    z-index:2147482540; display:none;
  }
  .rehab-backdrop.is-open { display:none; }
  .rehab-toast {
    position:fixed; left:50%; bottom:22px; transform:translateX(-50%) translateY(18px);
    z-index:2147482700; opacity:0; pointer-events:none; transition:.18s;
    display:flex; align-items:center; gap:9px; background:#0B0F19; color:#fff;
    border:1px solid rgba(255,255,255,.12); border-radius:12px; padding:11px 14px;
    box-shadow:0 18px 42px rgba(0,0,0,.24); font:700 13px var(--rehab-ui);
  }
  .rehab-toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
  html[data-rehab-shell] .rehab-workspace,
  html[data-rehab-shell] .rehab-role-workspace {
    width:100%; max-width:min(1560px, calc(100vw - 80px)); margin:0 auto;
  }
  html[data-rehab-shell] .rehab-role-head {
    display:flex; align-items:flex-end; justify-content:space-between; gap:24px;
    margin:0 0 20px;
  }
  html[data-rehab-shell] .rehab-role-head h1 {
    margin:0; color:var(--rehab-primary) !important;
    font:700 clamp(28px, 2.4vw, 38px)/1.08 var(--rehab-display) !important;
  }
  html[data-rehab-shell] .rehab-role-head p {
    margin:8px 0 0; max-width:720px; color:var(--rehab-muted) !important;
    font-size:14.5px !important; line-height:1.55 !important;
  }
  html[data-rehab-shell] .rehab-role-eyebrow {
    display:inline-flex; align-items:center; min-height:24px; margin-bottom:10px;
    padding:4px 10px; border:1px solid rgba(31,111,224,.20); border-radius:999px;
    color:var(--rehab-blue-strong); background:rgba(31,111,224,.10);
    font:800 11px/1 var(--rehab-ui); text-transform:uppercase; letter-spacing:.3px;
  }
  html[data-rehab-shell] .rehab-role-actions {
    display:flex; align-items:center; justify-content:flex-end; gap:8px; flex-wrap:wrap;
  }
  html[data-rehab-shell] .rehab-role-metrics {
    display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:16px; margin:0 0 24px;
  }
  html[data-rehab-shell] .rehab-role-metrics .rehab-metric-card {
    display:flex; flex-direction:column; gap:8px; min-height:112px; justify-content:center;
  }
  html[data-rehab-shell] .rehab-role-metrics .rehab-metric-card b {
    display:block; font:800 28px/1 var(--rehab-mono) !important; color:var(--rehab-primary) !important;
  }
  html[data-rehab-shell] .rehab-role-metrics .rehab-metric-card span {
    color:var(--rehab-secondary) !important; font:800 13px/1.25 var(--rehab-ui) !important;
  }
  html[data-rehab-shell] .rehab-role-metrics .rehab-metric-card small {
    color:var(--rehab-muted) !important; font:600 12px/1.35 var(--rehab-ui) !important;
  }
  html[data-rehab-shell] .rehab-section {
    margin:24px 0;
  }
  html[data-rehab-shell] .rehab-soft-card,
  html[data-rehab-shell] .rehab-data-card,
  html[data-rehab-shell] .rehab-table-shell,
  html[data-rehab-shell] .rehab-metric-card,
  html[data-rehab-shell] .metric-card,
  html[data-rehab-shell] .custom-card,
  html[data-rehab-shell] .info-box,
  html[data-rehab-shell] .card,
  html[data-rehab-shell] .stat,
  html[data-rehab-shell] [data-testid="stVerticalBlockBorderWrapper"],
  html[data-rehab-shell] div[data-testid="stExpander"],
  html[data-rehab-shell] [data-testid="stForm"],
  html[data-rehab-shell] [data-testid="stDataFrame"] {
    background:var(--rehab-card) !important;
    border:1px solid var(--rehab-line) !important;
    border-radius:8px !important;
    box-shadow:var(--rehab-shadow-sm) !important;
  }
  html[data-rehab-shell] .rehab-data-card,
  html[data-rehab-shell] .rehab-metric-card {
    padding:16px;
  }
  html[data-rehab-shell] .rehab-metric-card b,
  html[data-rehab-shell] .metric-card .metric-value,
  html[data-rehab-shell] .stat .value {
    font-family:var(--rehab-mono) !important;
    font-size:24px !important;
    line-height:1 !important;
    color:var(--rehab-primary) !important;
  }
  html[data-rehab-shell] .rehab-metric-card span,
  html[data-rehab-shell] .metric-card .metric-label,
  html[data-rehab-shell] .stat .label {
    color:var(--rehab-muted) !important;
    font-size:12.5px !important;
  }
  html[data-rehab-shell] .rehab-status {
    display:inline-flex; align-items:center; justify-content:center; min-height:24px;
    padding:4px 10px; border-radius:999px; font:800 12px var(--rehab-ui);
    background:var(--rehab-surface-3); color:var(--rehab-secondary);
  }
  html[data-rehab-shell] .rehab-status.success { background:rgba(5,150,105,.12); color:var(--rehab-success); }
  html[data-rehab-shell] .rehab-status.warning { background:rgba(217,119,6,.14); color:var(--rehab-warning); }
  html[data-rehab-shell] .rehab-status.danger { background:rgba(220,38,38,.12); color:var(--rehab-danger); }
  html[data-rehab-shell] .rehab-terminal-log,
  html[data-rehab-shell] pre.rehab-terminal-log {
    background:var(--ag-terminal-bg) !important; color:#38BDF8 !important;
    border:1px solid rgba(56,189,248,.22) !important; border-radius:8px !important;
    padding:16px !important; font:500 13px/1.45 var(--rehab-mono) !important;
    overflow:auto;
  }
  html[data-rehab-shell] .rehab-chat-row { display:flex; margin:16px 0; }
  html[data-rehab-shell] .rehab-chat-row.user { justify-content:flex-end; }
  html[data-rehab-shell] .rehab-chat-bubble {
    max-width:min(720px, 84vw); border-radius:8px; padding:12px 16px;
    background:var(--rehab-card); border:1px solid var(--rehab-line); color:var(--rehab-primary);
  }
  html[data-rehab-shell] .rehab-chat-row.user .rehab-chat-bubble {
    background:#E2E8F0; border-color:#E2E8F0; color:#0F172A;
  }
  html[data-rehab-shell] [data-testid="stDataFrame"] {
    overflow:hidden !important;
  }
  html[data-rehab-shell] [data-testid="stDataFrame"] iframe,
  html[data-rehab-shell] [data-testid="stDataFrame"] canvas {
    border-radius:8px !important;
  }
  html[data-rehab-shell] .stButton > button,
  html[data-rehab-shell] .stFormSubmitButton > button,
  html[data-rehab-shell] button[kind],
  html[data-rehab-shell] div[data-testid="stDownloadButton"] > button {
    border-radius:8px !important;
    min-height:40px !important;
    font:800 13px var(--rehab-ui) !important;
    transition:transform .14s ease, box-shadow .14s ease, border-color .14s ease !important;
  }
  html[data-rehab-shell] .stButton > button:hover,
  html[data-rehab-shell] .stFormSubmitButton > button:hover,
  html[data-rehab-shell] div[data-testid="stDownloadButton"] > button:hover {
    transform:translateY(-1px);
    box-shadow:var(--rehab-shadow-sm) !important;
  }
  html[data-rehab-shell] input,
  html[data-rehab-shell] textarea,
  html[data-rehab-shell] [contenteditable="true"] {
    font-family:var(--rehab-ui) !important;
  }
  html[data-rehab-shell] .stTextInput input,
  html[data-rehab-shell] .stTextArea textarea,
  html[data-rehab-shell] .stNumberInput input,
  html[data-rehab-shell] .stDateInput input {
    padding:12px 16px !important;
  }
  .rehab-auth-loading-root {
    position:fixed; inset:var(--rehab-topbar-h) 0 0 0; z-index:2147482400;
    display:grid; place-items:center; padding:28px;
    background:
      radial-gradient(60vw 50vh at 8% -8%, rgba(31,111,224,.12), transparent 60%),
      radial-gradient(55vw 50vh at 105% 0%, rgba(91,155,255,.10), transparent 55%),
      var(--rehab-bg);
  }
  .rehab-auth-loading-card {
    width:min(430px, calc(100vw - 40px)); border:1px solid var(--rehab-line);
    border-radius:20px; background:var(--rehab-card); box-shadow:var(--rehab-shadow);
    padding:28px; color:var(--rehab-primary); font-family:var(--rehab-ui);
  }
  .rehab-auth-loading-card b { display:block; font:800 20px/1.2 var(--rehab-display); margin-bottom:8px; }
  .rehab-auth-loading-card span { color:var(--rehab-muted); font-size:13px; }
  .rehab-auth-loading-pulse {
    width:40px; height:40px; border-radius:12px; display:grid; place-items:center; margin-bottom:16px;
    color:#fff; background:linear-gradient(145deg, var(--rehab-blue), var(--rehab-blue-strong));
    animation:rehabPulse 1.1s ease-in-out infinite;
  }
  @keyframes rehabPulse { 0%,100% { transform:scale(1); opacity:1; } 50% { transform:scale(.96); opacity:.72; } }
  html[data-rehab-shell] [data-testid="stVerticalBlockBorderWrapper"],
  html[data-rehab-shell] div[data-testid="stExpander"] { border-radius:8px !important; }
  html[data-rehab-shell] .ncv-stat-grid,
  html[data-rehab-shell] .ncv-patient-grid {
    display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:14px; margin:10px 0 22px;
  }
  html[data-rehab-shell] .ncv-stat-card,
  html[data-rehab-shell] .ncv-patient-card,
  html[data-rehab-shell] .ncv-table-card,
  html[data-rehab-shell] .ncv-filter-card,
  html[data-rehab-shell] .ncv-batch-card {
    background:var(--rehab-card) !important; border:1px solid var(--rehab-line) !important;
    border-radius:8px !important; box-shadow:var(--rehab-shadow-sm) !important;
  }
  html[data-rehab-shell] .ncv-stat-card { padding:18px; min-height:116px; }
  html[data-rehab-shell] .ncv-stat-top { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
  html[data-rehab-shell] .ncv-stat-ico {
    width:38px; height:38px; display:grid; place-items:center; border-radius:10px;
    color:var(--rehab-blue); background:rgba(37,110,217,.11);
  }
  html[data-rehab-shell] .ncv-stat-value {
    margin-top:16px; color:var(--rehab-primary); font:800 26px/1 var(--rehab-mono);
  }
  html[data-rehab-shell] .ncv-stat-label { margin-top:8px; color:var(--rehab-muted); font-size:12.5px; }
  html[data-rehab-shell] .ncv-stat-trend { color:var(--rehab-success); font:800 12px var(--rehab-ui); }
  html[data-rehab-shell] .ncv-section-label {
    display:flex; align-items:center; gap:8px; color:var(--rehab-primary); font:800 18px var(--rehab-ui);
    margin:22px 0 12px;
  }
  html[data-rehab-shell] .ncv-section-label .rehab-icon,
  html[data-rehab-shell] .ncv-section-label svg { color:var(--rehab-blue); width:18px; height:18px; }
  html[data-rehab-shell] .ncv-patient-card { display:flex; align-items:center; gap:14px; padding:16px; }
  html[data-rehab-shell] .ncv-avatar,
  html[data-rehab-shell] .ncv-table-avatar {
    width:38px; height:38px; border-radius:50%; display:grid; place-items:center;
    background:var(--rehab-blue); color:#fff; font:800 13px var(--rehab-ui); flex:none;
  }
  html[data-rehab-shell] .ncv-patient-card b,
  html[data-rehab-shell] .ncv-table-person b { color:var(--rehab-primary); font:800 13.5px/1.25 var(--rehab-ui); }
  html[data-rehab-shell] .ncv-patient-card span,
  html[data-rehab-shell] .ncv-table-person small { color:var(--rehab-muted); font-size:12px; line-height:1.35; }
  html[data-rehab-shell] .ncv-table-card { overflow:hidden; margin:10px 0 18px; }
  html[data-rehab-shell] .ncv-table-head {
    display:flex; justify-content:space-between; align-items:center; gap:14px; padding:14px 18px;
    border-bottom:1px solid var(--rehab-line); color:var(--rehab-primary);
  }
  html[data-rehab-shell] .ncv-table-head>div { display:flex; align-items:center; gap:8px; font-weight:800; }
  html[data-rehab-shell] .ncv-table-head svg { color:var(--rehab-blue); }
  html[data-rehab-shell] .ncv-table-head>span { color:var(--rehab-muted); font:800 12px var(--rehab-ui); }
  html[data-rehab-shell] .ncv-table-scroll { width:100%; overflow-x:auto; }
  html[data-rehab-shell] .ncv-table { width:100%; border-collapse:collapse; background:transparent; min-width:720px; }
  html[data-rehab-shell] .ncv-table th {
    padding:12px 18px; color:var(--rehab-muted); background:var(--rehab-bg-soft);
    border-bottom:1px solid var(--rehab-line); font:800 11px var(--rehab-ui); text-transform:uppercase; text-align:left;
  }
  html[data-rehab-shell] .ncv-table td {
    padding:13px 18px; color:var(--rehab-secondary); border-bottom:1px solid var(--rehab-line);
    font:500 13px/1.4 var(--rehab-ui); vertical-align:middle;
  }
  html[data-rehab-shell] .ncv-table tbody tr:hover { background:rgba(37,110,217,.05); }
  html[data-rehab-shell] .ncv-table-person { display:flex; align-items:center; gap:10px; min-width:210px; }
  html[data-rehab-shell] .ncv-table-person span:last-child { min-width:0; }
  html[data-rehab-shell] .ncv-vas,
  html[data-rehab-shell] .ncv-status {
    display:inline-flex; align-items:center; justify-content:center; min-height:24px; border-radius:999px;
    padding:4px 10px; font:800 12px var(--rehab-ui); white-space:nowrap;
  }
  html[data-rehab-shell] .ncv-vas.low { background:rgba(37,110,217,.13); color:var(--rehab-blue-strong); }
  html[data-rehab-shell] .ncv-vas.mid { background:rgba(217,119,6,.14); color:#9A5A00; }
  html[data-rehab-shell] .ncv-vas.high { background:rgba(220,38,38,.12); color:#B91C1C; }
  html[data-rehab-shell] .ncv-status.good { background:rgba(5,150,105,.12); color:#047857; }
  html[data-rehab-shell] .ncv-status.wait { background:rgba(100,116,139,.14); color:var(--rehab-secondary); }
  html[data-rehab-shell] .ncv-status.neutral { background:var(--rehab-bg-soft); color:var(--rehab-secondary); }
  html[data-rehab-shell] .ncv-row-arrow {
    width:34px; height:34px; border-radius:10px; border:1px solid var(--rehab-line);
    display:grid; place-items:center; color:var(--rehab-secondary); background:var(--rehab-card);
  }
  html[data-rehab-shell] .ncv-filter-card,
  html[data-rehab-shell] .ncv-batch-card { padding:16px; margin:10px 0 18px; }
  html[data-rehab-shell] .stTextInput div[data-baseweb="input"],
  html[data-rehab-shell] .stTextArea div[data-baseweb="textarea"],
  html[data-rehab-shell] .stNumberInput div[data-baseweb="input"],
  html[data-rehab-shell] .stDateInput div[data-baseweb="input"],
  html[data-rehab-shell] .stFileUploader section,
  html[data-rehab-shell] .stSelectbox div[data-baseweb="select"] > div {
    border-radius:8px !important;
    background:var(--rehab-bg-soft) !important;
    border-color:var(--rehab-line) !important;
    box-shadow:none !important;
  }
  html[data-rehab-shell] .stTextInput div[data-baseweb="input"]:focus-within,
  html[data-rehab-shell] .stTextArea div[data-baseweb="textarea"]:focus-within,
  html[data-rehab-shell] .stNumberInput div[data-baseweb="input"]:focus-within,
  html[data-rehab-shell] .stSelectbox div[data-baseweb="select"] > div:focus-within {
    border-color:var(--rehab-blue) !important;
    box-shadow:0 0 0 3px rgba(31,111,224,.12) !important;
  }
  html[data-rehab-theme="dark"] .stTextInput div[data-baseweb="input"] svg,
  html[data-rehab-theme="dark"] .stTextInput [data-testid="InputInstructions"],
  html[data-rehab-theme="dark"] .stTextInput [data-baseweb="input"] > div:first-child,
  html[data-rehab-theme="dark"] .stTextInput [data-baseweb="base-input"] > div:first-child {
    background:transparent !important;
    color:#E5EDF7 !important;
    border-color:transparent !important;
  }
  @media (max-width: 900px) {
    :root { --rehab-topbar-h:64px; --rehab-content-top:112px; --rehab-drawer-w:min(312px, 88vw); }
    .rehab-topbar { grid-template-columns:1fr auto; gap:10px; padding:10px 12px; }
    .rehab-tabs { grid-column:1 / -1; order:3; justify-content:flex-start; padding-top:8px; }
    .rehab-topbar:has(.rehab-tabs:not(:empty)) { min-height:112px; }
    .rehab-brand-mark { width:36px; height:36px; border-radius:10px; }
    .rehab-brand-name { font-size:15px; }
    .rehab-brand-sub { max-width:210px; }
    .rehab-rolebadge { display:none; }
    .rehab-user-meta { display:none; }
    .rehab-userchip { max-width:40px; }
    .rehab-drawer { top:112px; width:var(--rehab-drawer-w); }
    .rehab-drawer-fab { top:124px; }
    .rehab-backdrop { inset:112px 0 0 0; }
    .rehab-backdrop.is-open { display:block; }
    html[data-rehab-shell] .rehab-js-content-anchor { height:0 !important; }
    html[data-rehab-shell] [data-testid="stAppViewContainer"] > .main .block-container {
      padding-top:calc(var(--rehab-content-top) + 12px) !important;
      padding-left:18px!important;
      padding-right:18px!important;
      margin-left:auto!important;
      margin-right:auto!important;
    }
    html[data-rehab-shell][data-rehab-drawer-open="true"] [data-testid="stAppViewContainer"] > .main .block-container {
      max-width:100% !important;
      margin-left:auto!important;
      margin-right:auto!important;
    }
    #rehab-react-root,
    html[data-rehab-drawer-open="true"] #rehab-react-root {
      width:calc(100vw - 28px);
      margin:calc(var(--rehab-content-top) + 14px) 14px 18px;
    }
    .rehab-react-grid,
    .rehab-react-panel {
      grid-template-columns:1fr;
    }
    .rehab-react-title {
      display:block;
    }
    html[data-rehab-shell] .rehab-workspace,
    html[data-rehab-shell] .rehab-role-workspace {
      max-width:100% !important;
    }
    html[data-rehab-shell] .rehab-role-head {
      display:block;
      margin:4px 0 18px;
    }
    html[data-rehab-shell] .rehab-role-head h1 {
      font-size:clamp(25px,7vw,32px) !important;
    }
    html[data-rehab-shell] .rehab-role-head p {
      max-width:100%;
      font-size:13.5px !important;
    }
    html[data-rehab-shell] .ncv-stat-grid,
    html[data-rehab-shell] .ncv-patient-grid,
    html[data-rehab-shell] .rehab-role-metrics { grid-template-columns:1fr; }
  }
  @media (max-width: 520px) {
    .rehab-tabs { display:flex; }
    .rehab-tab { height:34px; padding:0 10px; font-size:12px; }
    .rehab-topbar:has(.rehab-tabs:empty) { min-height:64px !important; }
    .rehab-actions { gap:6px; max-width:46vw; }
    .rehab-icon-btn { width:36px; height:36px; border-radius:10px; }
    .rehab-drawer { top:112px; }
    .rehab-drawer-fab { top:124px; }
    .rehab-backdrop { inset:112px 0 0 0; }
    html[data-rehab-shell] .rehab-js-content-anchor { height:0 !important; }
  }
  `;

  const state = {
    payload: null,
    drawerOpen: false,
    lastEventId: 0,
    authRetryTimer: null,
    authRetryCount: 0,
    reactRetryTimer: null,
    reactRetryCount: 0,
  };

  function parentDoc() {
    try { return window.parent.document; } catch (_) { return document; }
  }

  function post(type, data) {
    window.parent.postMessage(Object.assign({ isStreamlitMessage: true, type }, data || {}), "*");
  }

  function ready() {
    post(MSG_READY, { apiVersion: 1 });
    post(MSG_HEIGHT, { height: 0 });
  }

  function sendEvent(event) {
    const payload = Object.assign({ id: Date.now() + "-" + (++state.lastEventId) }, event || {});
    post(MSG_VALUE, { value: payload, dataType: "json" });
  }

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function icon(id, cls) {
    return `<svg class="${cls || "rehab-icon"}" aria-hidden="true"><use href="#${esc(id)}"></use></svg>`;
  }

  function storage() {
    try { return JSON.parse(window.parent.localStorage.getItem(STORAGE_KEY) || "{}"); }
    catch (_) { return {}; }
  }

  function saveStorage(next) {
    try { window.parent.localStorage.setItem(STORAGE_KEY, JSON.stringify(Object.assign(storage(), next || {}))); }
    catch (_) {}
  }

  function ensureBase() {
    const doc = parentDoc();
    const root = doc.documentElement;
    root.dataset.rehabShell = "1";

    if (!doc.getElementById("rehab-ui-style")) {
      const style = doc.createElement("style");
      style.id = "rehab-ui-style";
      style.textContent = css;
      doc.head.appendChild(style);
    }
    if (!doc.getElementById("rehab-ui-sprite")) {
      const sprite = doc.createElement("div");
      sprite.id = "rehab-ui-sprite";
      sprite.innerHTML = iconSprite;
      doc.body.appendChild(sprite);
    }
    if (!doc.getElementById("rehab-topbar")) {
      const topbar = doc.createElement("div");
      topbar.id = "rehab-topbar";
      topbar.className = "rehab-topbar";
      doc.body.appendChild(topbar);
    }
    if (!doc.getElementById("rehab-drawer")) {
      const drawer = doc.createElement("aside");
      drawer.id = "rehab-drawer";
      drawer.className = "rehab-drawer";
      doc.body.appendChild(drawer);
    }
    if (!doc.getElementById("rehab-drawer-fab")) {
      const fab = doc.createElement("button");
      fab.id = "rehab-drawer-fab";
      fab.className = "rehab-drawer-fab is-hidden";
      fab.type = "button";
      fab.title = "Mở / thu sidebar";
      fab.setAttribute("aria-label", "Mở / thu sidebar");
      fab.addEventListener("click", () => setDrawer(!state.drawerOpen));
      doc.body.appendChild(fab);
    }
    if (!doc.getElementById("rehab-backdrop")) {
      const backdrop = doc.createElement("div");
      backdrop.id = "rehab-backdrop";
      backdrop.className = "rehab-backdrop";
      backdrop.addEventListener("click", () => setDrawer(false));
      doc.body.appendChild(backdrop);
    }
    if (!doc.getElementById("rehab-react-root")) {
      const reactRoot = doc.createElement("div");
      reactRoot.id = "rehab-react-root";
      reactRoot.setAttribute("aria-live", "polite");
      doc.body.insertBefore(reactRoot, doc.body.firstChild);
    }
    if (!doc.getElementById("rehab-toast")) {
      const toast = doc.createElement("div");
      toast.id = "rehab-toast";
      toast.className = "rehab-toast";
      doc.body.appendChild(toast);
    }
  }

  function initials(name, fallback) {
    const words = String(name || "").trim().split(/\s+/).filter(Boolean);
    if (!words.length) return fallback || "AI";
    return words.slice(-2).map((w) => w[0]).join("").toUpperCase().slice(0, 2);
  }

  function roleMeta(role) {
    const value = String(role || "");
    if (/quản|quan/i.test(value)) return { cls:"rb-qtv", icon:"i-cog", av:"QT", label:"Quản trị viên" };
    if (/nghiên|nghien|ncv/i.test(value)) return { cls:"rb-ncv", icon:"i-micro", av:"NC", label:"Nghiên cứu viên" };
    if (/bác|bac|ktv/i.test(value)) return { cls:"rb-doctor", icon:"i-stetho", av:"BS", label:"Bác sĩ / KTV PHCN" };
    return { cls:"rb-patient", icon:"i-heart", av:"BN", label:"Bệnh nhân" };
  }

  function routeWith(params) {
    const win = window.parent;
    const url = new URL(win.location.href);
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value == null || value === "") url.searchParams.delete(key);
      else url.searchParams.set(key, value);
    });
    return url.toString();
  }

  function applyTheme(theme) {
    const doc = parentDoc();
    const t = theme === "dark" ? "dark" : "light";
    doc.documentElement.dataset.rehabTheme = t;
    doc.documentElement.setAttribute("data-theme", t);
  }

  function normalizePayload(payload) {
    const next = Object.assign({}, payload || {});
    if (!next.mode) next.mode = next.loggedIn ? "app" : "auth";
    if (!next.theme) next.theme = parentDoc().documentElement.dataset.rehabTheme || "light";
    if (!Array.isArray(next.tabs)) next.tabs = [];
    if (!next.user || typeof next.user !== "object") next.user = {};
    return next;
  }

  function setDrawer(open) {
    state.drawerOpen = !!open;
    saveStorage({ drawerOpen: state.drawerOpen });
    const doc = parentDoc();
    doc.documentElement.dataset.rehabDrawerOpen = state.drawerOpen ? "true" : "false";
    const drawer = doc.getElementById("rehab-drawer");
    const backdrop = doc.getElementById("rehab-backdrop");
    const fab = doc.getElementById("rehab-drawer-fab");
    if (drawer) drawer.classList.toggle("is-open", state.drawerOpen);
    if (backdrop) backdrop.classList.toggle("is-open", state.drawerOpen);
    if (fab) {
      fab.classList.toggle("is-open", state.drawerOpen);
      fab.innerHTML = icon(state.drawerOpen ? "i-close" : "i-menu");
    }
  }

  function showToast(text) {
    const doc = parentDoc();
    const toast = doc.getElementById("rehab-toast");
    if (!toast) return;
    toast.innerHTML = `${icon("i-shield")}<span>${esc(text)}</span>`;
    toast.classList.add("show");
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => toast.classList.remove("show"), 2200);
  }

  function clearAuthRetry() {
    if (state.authRetryTimer) {
      clearTimeout(state.authRetryTimer);
      state.authRetryTimer = null;
    }
    state.authRetryCount = 0;
  }

  function removeAuthRoot() {
    const doc = parentDoc();
    const root = doc.getElementById("rehab-auth-root");
    if (root) root.remove();
  }

  function resetRoleShellForAuth() {
    const doc = parentDoc();
    delete doc.documentElement.dataset.rehabRoleUi;
    setDrawer(false);
    const drawer = doc.getElementById("rehab-drawer");
    const fab = doc.getElementById("rehab-drawer-fab");
    const backdrop = doc.getElementById("rehab-backdrop");
    const reactRoot = doc.getElementById("rehab-react-root");
    doc.documentElement.dataset.rehabDrawerOpen = "false";
    if (drawer) drawer.innerHTML = "";
    if (window.RehabReactApp && typeof window.RehabReactApp.unmount === "function") {
      try { window.RehabReactApp.unmount(reactRoot); } catch (_) {}
    }
    if (reactRoot) reactRoot.innerHTML = "";
    if (fab) fab.classList.add("is-hidden");
    if (backdrop) backdrop.classList.remove("is-open");
  }

  function renderAuthFallback(payload) {
    const doc = parentDoc();
    let root = doc.getElementById("rehab-auth-root");
    if (root && !root.classList.contains("rehab-auth-loading-root")) return;
    if (!root) {
      root = doc.createElement("main");
      root.id = "rehab-auth-root";
      doc.body.appendChild(root);
    }
    root.className = "rehab-auth-loading-root";
    root.innerHTML = `
      <div class="rehab-auth-loading-card" role="status" aria-live="polite">
        <div class="rehab-auth-loading-pulse">${icon("i-pulse")}</div>
        <b>Đang khởi tạo giao diện đăng nhập</b>
        <span>Rehab AI Monitor đang nạp form ${esc(payload.authMode || "login")}...</span>
      </div>
    `;
  }

  function renderTopbar(payload) {
    const doc = parentDoc();
    const topbar = doc.getElementById("rehab-topbar");
    const mode = payload.mode || "app";
    const user = payload.user || {};
    const role = roleMeta(user.role || payload.role);
    const tabs = Array.isArray(payload.tabs) ? payload.tabs : [];
    const active = payload.activeTab || "";
    const isAuth = mode === "auth";

    const tabsHtml = isAuth ? "" : tabs.map((tab) => `
      <button class="rehab-tab ${tab.id === active || tab.title === active ? "is-active" : ""}" data-tab="${esc(tab.id)}">
        ${icon(tab.icon || "i-doc")}<span>${esc(tab.label || tab.title || tab.id)}</span>
      </button>`).join("");

    topbar.innerHTML = `
      <div class="rehab-brand">
        <div class="rehab-brand-mark">${icon("i-pulse")}</div>
        <div class="rehab-brand-text">
          <div class="rehab-brand-name">Rehab <b>AI</b> Monitor</div>
          <div class="rehab-brand-sub">Hệ sinh thái lâm sàng · HUPH × BV Phạm Ngọc Thạch · 2026</div>
        </div>
      </div>
      <nav class="rehab-tabs" aria-label="Điều hướng vai trò">${tabsHtml}</nav>
      <div class="rehab-actions">
        ${isAuth ? "" : `<span class="rehab-rolebadge ${role.cls}">${icon(role.icon)}${esc(role.label)}</span>`}
        ${isAuth ? "" : `<div class="rehab-userchip"><div class="rehab-avatar">${esc(initials(user.full_name || user.username, role.av))}</div><div class="rehab-user-meta"><span class="rehab-user-name">${esc(user.full_name || user.username || "")}</span><span class="rehab-user-role">${esc(role.label)}</span></div></div>`}
        ${isAuth ? "" : `<button class="rehab-icon-btn" data-action="logout" title="Đăng xuất">${icon("i-logout")}</button>`}
        <button class="rehab-icon-btn" data-action="theme" title="Đổi giao diện sáng/tối">${icon(payload.theme === "dark" ? "i-sun" : "i-moon")}</button>
      </div>
    `;

    topbar.querySelectorAll("[data-tab]").forEach((btn) => {
      btn.addEventListener("click", () => sendEvent({ type: "tab", tab: btn.getAttribute("data-tab") }));
    });
    const logoutBtn = topbar.querySelector('[data-action="logout"]');
    if (logoutBtn) logoutBtn.addEventListener("click", () => sendEvent({ type: "logout" }));
    const themeBtn = topbar.querySelector('[data-action="theme"]');
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        const current = parentDoc().documentElement.dataset.rehabTheme || payload.theme || "light";
        const next = current === "dark" ? "light" : "dark";
        applyTheme(next);
        sendEvent({ type: "theme", theme: next });
      });
    }
  }

  function creditsHtml(sidebar) {
    const credits = sidebar.credits || {};
    return `
      <hr class="rehab-side-divider">
      <p><b>Giảng viên hướng dẫn 1:</b> ${esc(credits.mentor_data || "TS. Trần Hồng Việt")}</p>
      <p><b>Giảng viên hướng dẫn 2:</b> ${esc(credits.mentor_clinical || "Nguyễn Thị Thùy Chi")}</p>
      <p><b>${esc(credits.school || "Trường Đại học Y tế Công cộng")}</b></p>
      <p><b>Chủ nhiệm đề tài:</b> ${esc(credits.owner || "Đinh Lê Quỳnh Phương")}</p>
    `;
  }

  function sideFieldRange(key, label, value) {
    const safe = Number.isFinite(Number(value)) ? Number(value) : 0;
    return `<div class="rehab-side-field">
      <label>${icon("i-target")}${esc(label)}</label>
      <input type="range" min="0" max="1" step="0.01" value="${esc(safe)}" data-side-control="${esc(key)}">
      <div class="rehab-side-range-row"><span>0.00</span><span>${esc(safe.toFixed ? safe.toFixed(2) : safe)}</span><span>1.00</span></div>
    </div>`;
  }

  function sideSelect(key, label, value, options, labels) {
    const opts = (options || []).map((opt) => {
      const optionLabel = labels && labels[String(opt)] ? labels[String(opt)] : opt;
      return `<option value="${esc(opt)}" ${String(opt) === String(value) ? "selected" : ""}>${esc(optionLabel)}</option>`;
    }).join("");
    return `<div class="rehab-side-field">
      <label>${icon("i-cog")}${esc(label)}</label>
      <select class="rehab-side-select" data-side-control="${esc(key)}">${opts}</select>
    </div>`;
  }

  function roleHeader(sidebar, meta) {
    const profile = sidebar.profile || {};
    return `
      <div class="rehab-drawer-title">${icon(meta.icon)}VAI TRÒ</div>
      <div class="rehab-drawer-role">
        ${icon(meta.icon)}
        <div><b>${esc(meta.label)}</b><span>${esc(profile.full_name || profile.username || "Rehab AI Monitor")}</span></div>
      </div>
      ${sidebar.notice ? `<div class="rehab-side-result"><b>Thông báo:</b> ${esc(sidebar.notice)}</div>` : ""}
    `;
  }

  function researcherSidebar(payload, sidebar, meta) {
    const profile = sidebar.profile || payload.user || {};
    const stats = sidebar.stats || payload.sideStats || {};
    const controls = sidebar.controls || {};
    const opts = sidebar.options || {};
    return `
      ${roleHeader(sidebar, meta)}
      <div class="rehab-side-card">
        <h3>${icon("i-flask")}Thông tin chuyên gia</h3>
        <p><b>${esc(profile.full_name || "Đinh Lê Quỳnh Phương")}</b></p>
        <p>Trường Đại học Y tế Công cộng</p>
      </div>
      <div class="rehab-side-card">
        <h3>${icon("i-cog")}Cấu hình AI & tốc độ</h3>
        ${sideFieldRange("ncv_confidence", "Độ tự tin tối thiểu (Confidence)", controls.ncv_confidence ?? 0.5)}
        ${sideSelect("ncv_skip_frames", "Tốc độ xử lý", controls.ncv_skip_frames ?? 0, opts.skip_frames || [0,1,2,4], {
          0:"Tự động (theo độ dài video)", 1:"Nhanh (Bỏ qua 1 frame)", 2:"Nhanh (Bỏ qua 2 frame)", 4:"Nhanh (Bỏ qua 4 frame)"
        })}
        ${sideSelect("ncv_resize_width", "Độ phân giải video (Video Quality)", controls.ncv_resize_width ?? 480, opts.resize_width || [480,720,1080], {
          480:"480p (Tốc độ tối ưu)", 720:"720p (HD - Chuẩn sắc nét)", 1080:"1080p (Full HD - Cực kỳ chuẩn xác)"
        })}
        ${sideFieldRange("ncv_sensitivity", "Độ nhạy chuyển động (Sensitivity)", controls.ncv_sensitivity ?? 0.7)}
        ${sideSelect("ncv_giai_doan", "Giai đoạn tập bệnh nhân", controls.ncv_giai_doan || "Giai đoạn 2: Hồi phục (Sai số ±30°)", opts.phase_labels || [], null)}
      </div>
      <div class="rehab-side-card">
        <h3>${icon("i-bars")}Thống kê hệ thống</h3>
        <div class="rehab-kv"><span>Video chờ xử lý</span><b>${esc(stats.pending_ai ?? 0)}</b></div>
        <div class="rehab-kv"><span>Accuracy TB</span><b>${esc(stats.avg_acc ?? 0)}%</b></div>
        <div class="rehab-kv"><span>Tổng dữ liệu</span><b>${esc(stats.total_videos ?? 0)} Video</b></div>
      </div>
      <div class="rehab-side-card">
        <h3>${icon("i-target")}Chọn mô hình</h3>
        ${sideSelect("ncv_model_type", "Mô hình Pose", controls.ncv_model_type || "MediaPipe Heavy", opts.models || ["MediaPipe Heavy","MediaPipe Full","MediaPipe Lite"], null)}
        <hr class="rehab-side-divider">
        <h3>${icon("i-broom")}Làm mới tiến trình</h3>
        <p>Hủy tất cả tiến trình đang chạy/đang chờ để bắt đầu phân tích lại từ đầu.</p>
        <button class="rehab-side-button secondary" data-side-reset>${icon("i-broom")}Làm mới tiến trình</button>
        ${creditsHtml(sidebar)}
      </div>
    `;
  }

  function doctorSidebar(payload, sidebar, meta) {
    const profile = sidebar.profile || payload.user || {};
    const stats = sidebar.stats || payload.sideStats || {};
    return `
      ${roleHeader(sidebar, meta)}
      <div class="rehab-side-card">
        <h3>${icon("i-stetho")}Hồ sơ chuyên gia</h3>
        <p><b>${esc(profile.full_name || "Doctor 1")}</b></p>
        <p>Chuyên gia Phục hồi chức năng</p>
        <div class="rehab-kv"><span>Cơ sở</span><b>ĐH Y tế Công cộng</b></div>
        <div class="rehab-side-metrics">
          <div class="rehab-side-metric"><span>Chờ đánh giá</span><b>${esc(stats.pending ?? 0)}</b></div>
          <div class="rehab-side-metric"><span>Tổng bệnh nhân</span><b>${esc(stats.patients ?? 0)}</b></div>
        </div>
        ${creditsHtml(sidebar)}
      </div>
    `;
  }

  function patientSidebar(payload, sidebar, meta) {
    const profile = sidebar.profile || payload.user || {};
    return `
      ${roleHeader(sidebar, meta)}
      <div class="rehab-side-card">
        <h3>${icon("i-heart")}Xin chào, ${esc(profile.full_name || profile.username || "Bệnh nhân")}!</h3>
        <p>Bệnh nhân - Hệ thống PHCN AI</p>
      </div>
      <div class="rehab-side-card">
        <h3>${icon("i-doc")}Hướng dẫn sử dụng</h3>
        <p>Hệ thống hỗ trợ bạn qua các Tab sau:</p>
        <div class="rehab-side-guide">
          <div class="rehab-side-guide-item"><b>${icon("i-shield")}Trang chủ</b><span>Khai báo thông tin, triệu chứng, chọn bài tập và tải video tập luyện lên cho Bác sĩ.</span></div>
          <div class="rehab-side-guide-item"><b>${icon("i-bars")}Kết quả đánh giá</b><span>Xem nhận xét của Bác sĩ/KTV và kết quả phân tích AI về chuyển động của bạn.</span></div>
          <div class="rehab-side-guide-item"><b>${icon("i-bell")}Lịch nhắc nhở</b><span>Xem lịch tái khám và các nhắc nhở tập luyện hàng ngày.</span></div>
          <div class="rehab-side-guide-item"><b>${icon("i-doc")}Thông tin</b><span>Tìm hiểu về bài tập phục hồi chức năng vai và các kiến thức y tế hữu ích.</span></div>
          <div class="rehab-side-guide-item"><b>${icon("i-mail")}Liên hệ</b><span>Thông tin liên hệ với Bác sĩ/KTV khi cần hỗ trợ khẩn cấp.</span></div>
        </div>
        ${creditsHtml(sidebar)}
      </div>
    `;
  }

  function adminSidebar(payload, sidebar, meta) {
    const profile = sidebar.profile || payload.user || {};
    const search = sidebar.adminSearch || {};
    const result = search.result || null;
    const resultHtml = result ? (
      result.found
        ? `<div class="rehab-side-result"><b>${esc(result.full_name)}</b><br>${esc(result.username)} · ${esc(result.role)}${result.email ? `<br>${esc(result.email)}` : ""}</div>`
        : `<div class="rehab-side-result"><b>${esc(result.username || "")}</b><br>${esc(result.message || "Không tìm thấy người dùng.")}</div>`
    ) : "";
    return `
      ${roleHeader(sidebar, meta)}
      <div class="rehab-side-card">
        <h3>${icon("i-cog")}Quản trị hệ thống</h3>
        <p><b>${esc(profile.full_name || "System Administrator")}</b></p>
        <p>Quyền hạn tối cao (Super User)</p>
      </div>
      <div class="rehab-side-card">
        <h3>${icon("i-doc")}Chức năng các Tab quản trị</h3>
        <p><b>Trang chủ:</b> Dashboard thống kê, biểu đồ và chỉ số hiệu suất hệ thống.</p>
        <p><b>Quản trị:</b> Cấp tài khoản mới, xóa người dùng và reset database.</p>
        <p><b>Nhật ký:</b> Xem log hoạt động chi tiết của tất cả người dùng.</p>
        <p><b>Hướng dẫn:</b> Quản lý tài liệu và video hướng dẫn sử dụng.</p>
        <p><b>Kiến thức:</b> Thư viện nội dung chuyên môn về PHCN vai.</p>
        <p><b>Công nghệ:</b> Thông số kỹ thuật về hạ tầng AI và Computer Vision.</p>
      </div>
      <div class="rehab-side-card">
        <h3>${icon("i-search")}Tra cứu nhanh</h3>
        <div class="rehab-side-field">
          <label>${icon("i-user")}Tìm kiếm Username</label>
          <input class="rehab-side-input" data-admin-search-input value="${esc(search.query || "")}" placeholder="VD: patient01">
        </div>
        <button class="rehab-side-button secondary" data-admin-search>${icon("i-search")}Tra cứu</button>
        ${resultHtml}
        ${creditsHtml(sidebar)}
      </div>
    `;
  }

  function sidebarHtml(payload) {
    const meta = roleMeta(payload.role || (payload.user || {}).role);
    const sidebar = payload.sidebar || {};
    if (/Nghiên/.test(meta.label)) return researcherSidebar(payload, sidebar, meta);
    if (/Bác/.test(meta.label)) return doctorSidebar(payload, sidebar, meta);
    if (/Quản/.test(meta.label)) return adminSidebar(payload, sidebar, meta);
    return patientSidebar(payload, sidebar, meta);
  }

  function renderDrawer(payload) {
    const doc = parentDoc();
    const drawer = doc.getElementById("rehab-drawer");
    if (payload.mode === "auth") {
      drawer.innerHTML = "";
      const fab = doc.getElementById("rehab-drawer-fab");
      if (fab) fab.classList.add("is-hidden");
      setDrawer(false);
      return;
    }
    const fab = doc.getElementById("rehab-drawer-fab");
    if (fab) {
      fab.classList.remove("is-hidden");
      fab.innerHTML = icon(state.drawerOpen ? "i-close" : "i-menu");
    }
    drawer.innerHTML = sidebarHtml(payload);
    drawer.querySelectorAll("[data-side-control]").forEach((input) => {
      input.addEventListener("change", () => {
        sendEvent({ type: "side_control", key: input.getAttribute("data-side-control"), value: input.value });
      });
      if (input.type === "range") {
        input.addEventListener("input", () => {
          const row = input.parentElement && input.parentElement.querySelector(".rehab-side-range-row span:nth-child(2)");
          if (row) row.textContent = Number(input.value || 0).toFixed(2);
        });
      }
    });
    const resetBtn = drawer.querySelector("[data-side-reset]");
    if (resetBtn) resetBtn.addEventListener("click", () => sendEvent({ type: "side_reset_progress" }));
    const searchBtn = drawer.querySelector("[data-admin-search]");
    const searchInput = drawer.querySelector("[data-admin-search-input]");
    const runSearch = () => sendEvent({ type: "admin_user_search", username: searchInput ? searchInput.value : "" });
    if (searchBtn) searchBtn.addEventListener("click", runSearch);
    if (searchInput) {
      searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          runSearch();
        }
      });
    }
    setDrawer(state.drawerOpen);
  }

  function renderAuth(payload) {
    const mode = (payload && payload.mode) || "app";
    if (mode !== "auth") {
      clearAuthRetry();
      removeAuthRoot();
      return;
    }
    resetRoleShellForAuth();
    if (window.RehabAuthUI && typeof window.RehabAuthUI.mount === "function") {
      clearAuthRetry();
      try {
        window.RehabAuthUI.mount(payload, sendEvent, { icon, esc, showToast });
      } catch (error) {
        console.error("[RehabRuntime] Auth mount failed", error);
        renderAuthFallback(payload || {});
        showToast("Đang nạp lại giao diện đăng nhập...");
      }
      return;
    }
    renderAuthFallback(payload || {});
    if (state.authRetryCount >= 80 || state.authRetryTimer) return;
    state.authRetryCount += 1;
    state.authRetryTimer = setTimeout(() => {
      state.authRetryTimer = null;
      const latest = state.payload || {};
      if ((latest.mode || "app") === "auth") renderAuth(latest);
    }, state.authRetryCount < 12 ? 75 : 180);
  }

  function renderRoleChrome(payload) {
    if ((payload.mode || "app") === "auth") {
      resetRoleShellForAuth();
      return;
    }
    removeAuthRoot();
    const role = String(payload.role || (payload.user || {}).role || "");
    const key = /quản|quan/i.test(role) ? "Admin" :
      /bác|bac|ktv/i.test(role) ? "DoctorKtv" :
      /nghiên|nghien|ncv/i.test(role) ? "Researcher" : "Patient";
    const api = window["Rehab" + key + "UI"];
    if (api && typeof api.mount === "function") {
      api.mount(payload, sendEvent, { icon, esc, showToast });
    }
  }

  function renderReactApp(payload) {
    const doc = parentDoc();
    const root = doc.getElementById("rehab-react-root");
    if (!root) return;
    if ((payload.mode || "app") === "auth") {
      if (state.reactRetryTimer) {
        clearTimeout(state.reactRetryTimer);
        state.reactRetryTimer = null;
      }
      state.reactRetryCount = 0;
      if (window.RehabReactApp && typeof window.RehabReactApp.unmount === "function") {
        try { window.RehabReactApp.unmount(root); } catch (_) {}
      }
      root.innerHTML = "";
      return;
    }
    if (window.RehabReactApp && typeof window.RehabReactApp.mount === "function") {
      if (state.reactRetryTimer) {
        clearTimeout(state.reactRetryTimer);
        state.reactRetryTimer = null;
      }
      state.reactRetryCount = 0;
      try {
        window.RehabReactApp.mount(root, payload, sendEvent, { icon, esc, showToast });
      } catch (error) {
        console.error("[RehabRuntime] React role app mount failed", error);
      }
      return;
    }
    if (state.reactRetryCount < 60 && !state.reactRetryTimer) {
      state.reactRetryCount += 1;
      state.reactRetryTimer = setTimeout(() => {
        state.reactRetryTimer = null;
        renderReactApp(state.payload || payload);
      }, state.reactRetryCount < 10 ? 80 : 220);
    }
  }

  function mount(payload) {
    state.payload = normalizePayload(payload);
    ensureBase();
    parentDoc().documentElement.dataset.rehabMode = state.payload.mode || "app";
    const stored = storage();
    if (typeof stored.drawerOpen === "boolean") state.drawerOpen = stored.drawerOpen;
    applyTheme(state.payload.theme || "light");
    renderTopbar(state.payload);
    renderDrawer(state.payload);
    renderAuth(state.payload);
    renderRoleChrome(state.payload);
    renderReactApp(state.payload);
    setDrawer(state.drawerOpen && state.payload.mode !== "auth");
  }

  window.addEventListener("message", (event) => {
    if (!event.data || event.data.type !== MSG_RENDER) return;
    const args = event.data.args || {};
    mount(args.payload || {});
  });

  window.RehabRuntime = { mount, sendEvent, showToast, routeWith };
  ready();
})();
