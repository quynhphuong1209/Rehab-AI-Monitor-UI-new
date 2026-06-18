(function () {
  const css = `
  html[data-rehab-role-ui="researcher"] [data-testid="stAppViewContainer"] > .main .block-container {
    max-width: 1120px !important;
  }
  html[data-rehab-role-ui="researcher"] .ncv-table-card,
  html[data-rehab-role-ui="researcher"] .ncv-stat-card,
  html[data-rehab-role-ui="researcher"] .ncv-patient-card {
    border-radius: 8px !important;
    border-color: var(--rehab-line) !important;
    background: var(--rehab-card) !important;
    box-shadow: var(--rehab-shadow-sm) !important;
  }
  html[data-rehab-role-ui="researcher"] .ncv-table-head,
  html[data-rehab-role-ui="researcher"] .ncv-section-label {
    color: var(--rehab-primary) !important;
  }
  html[data-rehab-role-ui="researcher"] .stButton > button,
  html[data-rehab-role-ui="researcher"] .stFormSubmitButton > button {
    border-radius: 8px !important;
    font-weight: 800 !important;
  }
  `;

  function doc() {
    try { return window.parent.document; } catch (_) { return document; }
  }

  function mount() {
    const d = doc();
    if (!d.getElementById("rehab-researcher-ui-style")) {
      const style = d.createElement("style");
      style.id = "rehab-researcher-ui-style";
      style.textContent = css;
      d.head.appendChild(style);
    }
    d.documentElement.dataset.rehabRoleUi = "researcher";
  }

  window.RehabResearcherUI = { mount };
})();
