(function () {
  const css = `
  html[data-rehab-role-ui="admin"] [data-testid="stAppViewContainer"] > .main .block-container {
    max-width: 1120px !important;
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
