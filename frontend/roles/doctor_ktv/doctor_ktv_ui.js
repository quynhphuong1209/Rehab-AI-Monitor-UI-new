(function () {
  const css = `
  html[data-rehab-role-ui="doctor_ktv"] [data-testid="stAppViewContainer"] > .main .block-container {
    max-width: none !important;
  }
  html[data-rehab-role-ui="doctor_ktv"] .rehab-role-eyebrow {
    color:var(--rehab-blue-strong); border-color:rgba(31,111,224,.24); background:rgba(31,111,224,.10);
  }
  html[data-rehab-role-ui="doctor_ktv"] [data-testid="stDataFrame"],
  html[data-rehab-role-ui="doctor_ktv"] .ncv-table-card,
  html[data-rehab-role-ui="doctor_ktv"] .ncv-patient-card,
  html[data-rehab-role-ui="doctor_ktv"] .ncv-filter-card,
  html[data-rehab-role-ui="doctor_ktv"] .ncv-select-panel,
  html[data-rehab-role-ui="doctor_ktv"] .ncv-selected-video-card,
  html[data-rehab-role-ui="doctor_ktv"] .ncv-detail-panel,
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
  html[data-rehab-role-ui="doctor_ktv"] [data-testid="stDataFrame"],
  html[data-rehab-role-ui="doctor_ktv"] div[data-testid="stExpander"] {
    margin-bottom:16px !important;
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
