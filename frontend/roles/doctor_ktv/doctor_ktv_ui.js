(function () {
  const css = `
  html[data-rehab-role-ui="doctor_ktv"] [data-testid="stAppViewContainer"] > .main .block-container {
    max-width: 1120px !important;
  }
  html[data-rehab-role-ui="doctor_ktv"] [data-testid="stDataFrame"],
  html[data-rehab-role-ui="doctor_ktv"] .ncv-table-card,
  html[data-rehab-role-ui="doctor_ktv"] .ncv-patient-card,
  html[data-rehab-role-ui="doctor_ktv"] .card,
  html[data-rehab-role-ui="doctor_ktv"] [data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 8px !important;
    border-color: var(--rehab-line) !important;
    background: var(--rehab-card) !important;
    box-shadow: var(--rehab-shadow-sm) !important;
  }
  html[data-rehab-role-ui="doctor_ktv"] .stButton > button,
  html[data-rehab-role-ui="doctor_ktv"] .stFormSubmitButton > button {
    border-radius: 8px !important;
    font-weight: 800 !important;
  }
  `;

  function doc() {
    try { return window.parent.document; } catch (_) { return document; }
  }

  function mount() {
    const d = doc();
    if (!d.getElementById("rehab-doctor-ktv-ui-style")) {
      const style = d.createElement("style");
      style.id = "rehab-doctor-ktv-ui-style";
      style.textContent = css;
      d.head.appendChild(style);
    }
    d.documentElement.dataset.rehabRoleUi = "doctor_ktv";
  }

  window.RehabDoctorKtvUI = { mount };
})();
