(function () {
  const css = `
  html[data-rehab-role-ui="admin"] [data-testid="stAppViewContainer"] > .main .block-container {
    max-width: none !important;
    width: calc(100vw - 24px) !important;
    margin-left: 12px !important;
    margin-right: 12px !important;
    padding-top: calc(var(--rehab-topbar-h, 72px) + 10px) !important;
  }
  html[data-rehab-role-ui="admin"] .rehab-role-eyebrow {
    color:var(--rehab-warning); border-color:rgba(217,119,6,.24); background:rgba(217,119,6,.10);
  }
  html[data-rehab-shell] .admin-dashboard,
  html[data-rehab-shell] .duk .page-head,
  html[data-rehab-shell] .metric-card {
    font-family: var(--rehab-ui) !important;
  }
  html[data-rehab-shell] .metric-card,
  html[data-rehab-shell] .stat,
  html[data-rehab-shell] .card,
  html[data-rehab-role-ui="admin"] [data-testid="stVerticalBlockBorderWrapper"],
  html[data-rehab-role-ui="admin"] .ncv-table-card {
    border-radius: 8px !important;
    border-color: var(--rehab-line) !important;
    background: var(--rehab-card) !important;
    box-shadow: var(--rehab-shadow-sm) !important;
  }
  html[data-rehab-role-ui="admin"] .stButton > button,
  html[data-rehab-role-ui="admin"] .stFormSubmitButton > button {
    border-radius: 8px !important;
    font-weight: 800 !important;
  }
  html[data-rehab-role-ui="admin"] .duk {
    max-width:100% !important;
  }
  html[data-rehab-role-ui="admin"] .grid {
    gap:16px !important;
  }
  `;

  function doc() {
    try { return window.parent.document; } catch (_) { return document; }
  }

  function mount(payload) {
    const d = doc();
    if (!d.getElementById("rehab-admin-ui-style")) {
      const style = d.createElement("style");
      style.id = "rehab-admin-ui-style";
      style.textContent = css;
      d.head.appendChild(style);
    }
    d.documentElement.dataset.rehabRoleUi = "admin";
  }

  window.RehabAdminUI = { mount };
})();
