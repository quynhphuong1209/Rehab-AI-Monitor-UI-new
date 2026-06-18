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
    --rehab-blue:#256ED9;
    --rehab-blue-strong:#1E5FC4;
    --rehab-accent:#0284C7;
    --rehab-success:#059669;
    --rehab-warning:#D97706;
    --rehab-danger:#DC2626;
    --rehab-bg:#EAF1FA;
    --rehab-bg-soft:#F8FAFC;
    --rehab-card:#FFFFFF;
    --rehab-line:#D6E1F0;
    --rehab-muted:#64748B;
    --rehab-shadow:0 22px 50px rgba(15,23,42,.12);
    --rehab-shadow-sm:0 2px 8px rgba(15,23,42,.08);
    --rehab-ui:Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --rehab-display:"Fraunces", Georgia, serif;
    --rehab-mono:"JetBrains Mono", "Fira Code", monospace;
    --rehab-r:8px;
    --rehab-r-lg:20px;
    --rehab-topbar-h:72px;
  }
  html[data-rehab-theme="dark"] {
    --rehab-primary:#E5EDF7;
    --rehab-secondary:#A9B8CB;
    --rehab-bg:#0B111B;
    --rehab-bg-soft:#111B2A;
    --rehab-card:#101A29;
    --rehab-line:#243348;
    --rehab-muted:#93A4B8;
    --rehab-shadow:0 22px 50px rgba(0,0,0,.34);
    --rehab-shadow-sm:0 2px 8px rgba(0,0,0,.24);
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
  html[data-rehab-shell] [data-testid="stAppViewContainer"] > .main .block-container {
    padding-top: 0 !important;
    max-width: 1120px !important;
    margin-left: auto !important;
    margin-right: auto !important;
  }
  html[data-rehab-shell] .rehab-js-content-anchor { height:74px !important; }
  html[data-rehab-shell] h1,
  html[data-rehab-shell] h2,
  html[data-rehab-shell] h3 {
    color: var(--rehab-primary) !important;
    letter-spacing: 0 !important;
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
    position:fixed; z-index:2147482565; left:12px; top:calc(var(--rehab-topbar-h) + 12px);
    width:38px; height:38px; border-radius:12px; border:1px solid var(--rehab-line);
    background:var(--rehab-card); color:var(--rehab-blue-strong);
    display:grid; place-items:center; cursor:pointer; box-shadow:var(--rehab-shadow-sm);
    transition:transform .16s ease, opacity .16s ease, border-color .16s ease;
  }
  .rehab-drawer-fab:hover { transform:translateY(-1px); border-color:var(--rehab-blue); }
  .rehab-drawer-fab.is-hidden { display:none; }
  .rehab-drawer {
    position:fixed; z-index:2147482550; top:var(--rehab-topbar-h); left:0; bottom:0; width:286px;
    background:rgba(248,250,252,.96); border-right:1px solid var(--rehab-line);
    box-shadow:14px 0 34px rgba(15,23,42,.08); transform:translateX(-104%);
    transition:transform .2s ease; padding:18px 14px; overflow-y:auto;
  }
  html[data-rehab-theme="dark"] .rehab-drawer { background:rgba(11,17,27,.96); }
  .rehab-drawer.is-open { transform:translateX(0); }
  .rehab-drawer-title { font-size:11px; text-transform:uppercase; letter-spacing:.7px; color:var(--rehab-muted); font-weight:800; margin:2px 10px 10px; }
  .rehab-drawer .rehab-tab { width:100%; justify-content:flex-start; border-radius:11px; margin-bottom:4px; }
  .rehab-drawer .rehab-tab.is-active { box-shadow:inset 3px 0 0 var(--rehab-blue); }
  .rehab-side-card {
    margin-top:18px; background:var(--rehab-card); border:1px solid var(--rehab-line);
    border-radius:8px; padding:14px; box-shadow:var(--rehab-shadow-sm);
  }
  .rehab-side-card h3 { display:flex; align-items:center; gap:8px; margin:0 0 10px; font-size:13px; }
  .rehab-kv { display:flex; justify-content:space-between; gap:12px; padding:5px 0; color:var(--rehab-secondary); font-size:12.5px; }
  .rehab-kv b { color:var(--rehab-primary); font-family:var(--rehab-mono); }
  .rehab-backdrop {
    position:fixed; inset:var(--rehab-topbar-h) 0 0 0; background:rgba(15,23,42,.22);
    z-index:2147482540; display:none;
  }
  .rehab-backdrop.is-open { display:block; }
  .rehab-toast {
    position:fixed; left:50%; bottom:22px; transform:translateX(-50%) translateY(18px);
    z-index:2147482700; opacity:0; pointer-events:none; transition:.18s;
    display:flex; align-items:center; gap:9px; background:#0B0F19; color:#fff;
    border:1px solid rgba(255,255,255,.12); border-radius:12px; padding:11px 14px;
    box-shadow:0 18px 42px rgba(0,0,0,.24); font:700 13px var(--rehab-ui);
  }
  .rehab-toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
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
  html[data-rehab-shell] .stSelectbox div[data-baseweb="select"] > div {
    border-radius:8px !important;
    background:var(--rehab-bg-soft) !important;
    border-color:var(--rehab-line) !important;
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
    :root { --rehab-topbar-h:64px; }
    .rehab-topbar { grid-template-columns:1fr auto; gap:10px; padding:10px 12px; }
    .rehab-tabs { grid-column:1 / -1; order:3; justify-content:flex-start; padding-top:8px; }
    .rehab-topbar:has(.rehab-tabs:not(:empty)) { min-height:112px; }
    .rehab-brand-mark { width:36px; height:36px; border-radius:10px; }
    .rehab-brand-name { font-size:15px; }
    .rehab-brand-sub { max-width:210px; }
    .rehab-rolebadge { display:none; }
    .rehab-user-meta { display:none; }
    .rehab-userchip { max-width:40px; }
    .rehab-drawer { top:112px; width:min(286px, 86vw); }
    .rehab-drawer-fab { top:124px; }
    .rehab-backdrop { inset:112px 0 0 0; }
    html[data-rehab-shell] .rehab-js-content-anchor { height:112px !important; }
    html[data-rehab-shell] [data-testid="stAppViewContainer"] > .main .block-container { padding-left:18px!important; padding-right:18px!important; }
    html[data-rehab-shell] .ncv-stat-grid,
    html[data-rehab-shell] .ncv-patient-grid { grid-template-columns:1fr; }
  }
  @media (max-width: 520px) {
    .rehab-tabs { display:flex; }
    .rehab-tab { height:34px; padding:0 10px; font-size:12px; }
    .rehab-topbar:has(.rehab-tabs:empty) { min-height:64px !important; }
    .rehab-drawer { top:112px; }
    .rehab-drawer-fab { top:124px; }
    .rehab-backdrop { inset:112px 0 0 0; }
    html[data-rehab-shell] .rehab-js-content-anchor { height:112px !important; }
    html[data-rehab-shell] .rehab-topbar:has(.rehab-tabs:empty) ~ .rehab-js-content-anchor { height:64px !important; }
  }
  `;

  const state = { payload: null, drawerOpen: false, lastEventId: 0 };

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

  function setDrawer(open) {
    state.drawerOpen = !!open;
    saveStorage({ drawerOpen: state.drawerOpen });
    const doc = parentDoc();
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
        ${isAuth ? "" : `<button class="rehab-icon-btn" data-action="drawer" title="Mở / thu sidebar">${icon("i-menu")}</button>`}
        ${isAuth ? "" : `<span class="rehab-rolebadge ${role.cls}">${icon(role.icon)}${esc(role.label)}</span>`}
        ${isAuth ? "" : `<div class="rehab-userchip"><div class="rehab-avatar">${esc(initials(user.full_name || user.username, role.av))}</div><div class="rehab-user-meta"><span class="rehab-user-name">${esc(user.full_name || user.username || "")}</span><span class="rehab-user-role">${esc(role.label)}</span></div></div>`}
        ${isAuth ? "" : `<button class="rehab-icon-btn" data-action="logout" title="Đăng xuất">${icon("i-logout")}</button>`}
        <button class="rehab-icon-btn" data-action="theme" title="Đổi giao diện sáng/tối">${icon(payload.theme === "dark" ? "i-sun" : "i-moon")}</button>
      </div>
    `;

    topbar.querySelectorAll("[data-tab]").forEach((btn) => {
      btn.addEventListener("click", () => sendEvent({ type: "tab", tab: btn.getAttribute("data-tab") }));
    });
    const drawerBtn = topbar.querySelector('[data-action="drawer"]');
    if (drawerBtn) drawerBtn.addEventListener("click", () => setDrawer(!state.drawerOpen));
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

  function sideStats(payload) {
    const role = roleMeta(payload.role || (payload.user || {}).role).label;
    const stats = payload.sideStats || {};
    if (/Nghiên/.test(role)) {
      return [
        ["Video mẫu", stats.total_videos ?? "8"],
        ["Có kết quả AI", stats.ai_done ?? "8"],
        ["Mô hình", stats.model ?? "MP-Heavy"],
        ["Điểm/khung", stats.keypoints ?? "33"],
      ];
    }
    if (/Bác/.test(role)) {
      return [
        ["BN phụ trách", stats.patients ?? "18"],
        ["Chờ đánh giá", stats.pending ?? "3"],
        ["VAS ≥ 6", stats.high_vas ?? "2"],
        ["Buổi tập 7 ngày", stats.sessions ?? "126"],
      ];
    }
    if (/Quản/.test(role)) {
      return [
        ["Tài khoản", stats.accounts ?? "24"],
        ["Video hệ thống", stats.videos ?? "14"],
        ["Đánh giá", stats.evals ?? "63"],
        ["Theme", payload.theme || "light"],
      ];
    }
    return [
      ["Chẩn đoán", stats.diagnosis ?? "Theo hồ sơ"],
      ["Tuần điều trị", stats.week ?? "Đang theo dõi"],
      ["VAS hôm nay", stats.vas ?? "N/A"],
      ["Bác sĩ", stats.doctor ?? "Bác sĩ / KTV"],
    ];
  }

  function renderDrawer(payload) {
    const doc = parentDoc();
    const drawer = doc.getElementById("rehab-drawer");
    const tabs = Array.isArray(payload.tabs) ? payload.tabs : [];
    const active = payload.activeTab || "";
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
    const nav = tabs.map((tab) => `
      <button class="rehab-tab ${tab.id === active || tab.title === active ? "is-active" : ""}" data-tab="${esc(tab.id)}">
        ${icon(tab.icon || "i-doc")}<span>${esc(tab.label || tab.title || tab.id)}</span>
      </button>`).join("");
    const stats = sideStats(payload).map(([k, v]) => `<div class="rehab-kv"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join("");
    drawer.innerHTML = `
      <div class="rehab-drawer-title">Điều hướng</div>
      <nav>${nav}</nav>
      <div class="rehab-side-card">
        <h3>${icon("i-db")}Tổng quan phiên</h3>
        ${stats}
      </div>
    `;
    drawer.querySelectorAll("[data-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        setDrawer(false);
        sendEvent({ type: "tab", tab: btn.getAttribute("data-tab") });
      });
    });
    setDrawer(state.drawerOpen);
  }

  function renderAuth(payload) {
    if (window.RehabAuthUI && typeof window.RehabAuthUI.mount === "function") {
      window.RehabAuthUI.mount(payload, sendEvent, { icon, esc, showToast });
    }
  }

  function renderRoleChrome(payload) {
    const role = String(payload.role || (payload.user || {}).role || "");
    const key = /quản|quan/i.test(role) ? "Admin" :
      /bác|bac|ktv/i.test(role) ? "DoctorKtv" :
      /nghiên|nghien|ncv/i.test(role) ? "Researcher" : "Patient";
    const api = window["Rehab" + key + "UI"];
    if (api && typeof api.mount === "function") {
      api.mount(payload, sendEvent, { icon, esc, showToast });
    }
  }

  function mount(payload) {
    state.payload = payload || {};
    ensureBase();
    const stored = storage();
    if (typeof stored.drawerOpen === "boolean") state.drawerOpen = stored.drawerOpen;
    applyTheme(state.payload.theme || "light");
    renderTopbar(state.payload);
    renderDrawer(state.payload);
    renderAuth(state.payload);
    renderRoleChrome(state.payload);
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
