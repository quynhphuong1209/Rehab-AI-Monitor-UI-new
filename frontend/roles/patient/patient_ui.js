(function () {
  const css = `
  html[data-rehab-role-ui="patient"] [data-testid="stAppViewContainer"] > .main .block-container {
    max-width: 1120px !important;
  }
  html[data-rehab-role-ui="patient"] [data-testid="stVerticalBlockBorderWrapper"],
  html[data-rehab-role-ui="patient"] .ncv-table-card,
  html[data-rehab-role-ui="patient"] .ncv-patient-card,
  html[data-rehab-role-ui="patient"] .custom-card,
  html[data-rehab-role-ui="patient"] .info-box {
    border-radius: 8px !important;
    border-color: var(--rehab-line) !important;
    background: var(--rehab-card) !important;
    box-shadow: var(--rehab-shadow-sm) !important;
  }
  html[data-rehab-role-ui="patient"] .stButton > button,
  html[data-rehab-role-ui="patient"] .stFormSubmitButton > button {
    border-radius: 8px !important;
    font-weight: 800 !important;
  }
  `;

  function doc() {
    try { return window.parent.document; } catch (_) { return document; }
  }

  function mount() {
    const d = doc();
    if (!d.getElementById("rehab-patient-ui-style")) {
      const style = d.createElement("style");
      style.id = "rehab-patient-ui-style";
      style.textContent = css;
      d.head.appendChild(style);
    }
    d.documentElement.dataset.rehabRoleUi = "patient";
  }

  window.RehabPatientUI = { mount };
})();
