(function () {
  const css = `
  .rehab-auth-root {
    position:fixed; z-index:2147482400; left:0; right:0; top:var(--rehab-topbar-h); bottom:0;
    overflow:auto; background:
      radial-gradient(48vw 44vh at 12% 4%, rgba(37,110,217,.10), transparent 62%),
      radial-gradient(48vw 44vh at 96% 0%, rgba(99,102,241,.10), transparent 58%),
      var(--rehab-bg);
  }
  .rehab-auth-wrap {
    min-height:calc(100vh - var(--rehab-topbar-h));
    display:grid; grid-template-columns:minmax(420px, 1.08fr) minmax(360px, .92fr);
    align-items:center; gap:clamp(24px,4vw,62px);
    padding:clamp(28px,5vw,64px) clamp(24px,5vw,68px);
  }
  .rehab-auth-hero { position:relative; min-height:520px; display:flex; flex-direction:column; justify-content:center; gap:24px; }
  .rehab-auth-eyebrow {
    display:inline-flex; align-items:center; gap:8px; align-self:flex-start;
    padding:6px 13px; border-radius:999px; font-size:12px; font-weight:800; letter-spacing:.2px;
    color:var(--rehab-blue-strong); background:rgba(37,110,217,.13); border:1px solid rgba(37,110,217,.20);
  }
  .rehab-auth-hero h1 {
    margin:0; max-width:880px; color:var(--rehab-primary);
    font-family:var(--rehab-display); font-weight:650; font-size:clamp(42px,5.2vw,66px);
    line-height:1.03; letter-spacing:0;
  }
  .rehab-auth-hero h1 em { color:var(--rehab-blue); font-style:italic; white-space:nowrap; }
  .rehab-auth-hero p {
    margin:0; max-width:50ch; color:var(--rehab-secondary); font-size:17px; line-height:1.55;
  }
  .rehab-auth-stats { display:flex; flex-wrap:wrap; gap:14px; }
  .rehab-auth-stat {
    background:var(--rehab-card); border:1px solid var(--rehab-line); border-radius:8px;
    min-width:150px; padding:15px 17px; box-shadow:var(--rehab-shadow-sm);
  }
  .rehab-auth-stat b { display:block; color:var(--rehab-blue-strong); font:800 24px var(--rehab-mono); }
  .rehab-auth-stat span { display:block; color:var(--rehab-muted); font-size:12px; margin-top:4px; }
  .rehab-pose { position:absolute; right:-12px; bottom:0; width:min(42%,360px); opacity:.94; pointer-events:none; }
  .rehab-pose svg { width:100%; height:auto; overflow:visible; }
  .rehab-pose .bone { stroke:var(--rehab-blue); stroke-width:5; stroke-linecap:round; fill:none; }
  .rehab-pose .bone.dim { stroke:var(--rehab-muted); opacity:.35; }
  .rehab-pose .joint { fill:var(--rehab-card); stroke:var(--rehab-blue); stroke-width:3.4; }
  .rehab-pose .joint.dim { stroke:var(--rehab-muted); opacity:.45; }
  .rehab-pose .arc { stroke:#7773FF; stroke-width:4; fill:none; stroke-linecap:round; opacity:.85; }
  .rehab-pose #rehabPoseArm { transform-box:fill-box; transform-origin:left top; }
  @media (prefers-reduced-motion:no-preference){ .rehab-pose #rehabPoseArm { animation:rehab-arm 4.4s ease-in-out infinite; } }
  @keyframes rehab-arm { 0%,100%{transform:rotate(2deg)} 50%{transform:rotate(-44deg)} }
  .rehab-auth-panel { display:flex; justify-content:center; align-items:center; }
  .rehab-auth-card {
    width:100%; max-width:430px; background:var(--rehab-card); border:1px solid var(--rehab-line);
    border-radius:20px; box-shadow:var(--rehab-shadow); padding:34px;
  }
  .rehab-auth-card h2 { font-family:var(--rehab-display); font-size:25px; line-height:1.12; margin:0 0 6px; color:var(--rehab-primary); }
  .rehab-auth-sub { margin:0 0 22px; color:var(--rehab-muted); font-size:13.5px; }
  .rehab-seg { display:flex; gap:4px; background:var(--rehab-bg-soft); border:1px solid var(--rehab-line); border-radius:12px; padding:4px; margin-bottom:22px; }
  .rehab-seg button {
    flex:1; height:34px; border:0; border-radius:9px; background:transparent; color:var(--rehab-muted);
    font:800 13.5px var(--rehab-ui); cursor:pointer;
  }
  .rehab-seg button.on { background:var(--rehab-card); color:var(--rehab-blue-strong); box-shadow:var(--rehab-shadow-sm); }
  .rehab-role-label, .rehab-field label {
    display:block; margin:0 0 7px; color:var(--rehab-secondary); font:800 12.5px var(--rehab-ui);
  }
  .rehab-role-grid { display:grid; grid-template-columns:1fr 1fr; gap:9px; margin-bottom:18px; }
  .rehab-role-opt {
    display:flex; align-items:center; gap:10px; min-height:58px; text-align:left;
    padding:10px; border:1.5px solid var(--rehab-line); border-radius:13px;
    background:var(--rehab-bg-soft); color:var(--rehab-primary); cursor:pointer; transition:.16s;
  }
  .rehab-role-opt:hover { border-color:var(--rehab-blue); transform:translateY(-1px); }
  .rehab-role-opt.on { border-color:var(--rehab-blue); background:rgba(37,110,217,.11); box-shadow:0 0 0 3px rgba(37,110,217,.12); }
  .rehab-role-opt.full { grid-column:1 / -1; }
  .rehab-role-icon {
    width:34px; height:34px; border-radius:10px; display:grid; place-items:center;
    background:var(--rehab-card); border:1px solid var(--rehab-line); color:var(--rehab-secondary); flex:none;
  }
  .rehab-role-opt.on .rehab-role-icon { background:var(--rehab-blue); border-color:var(--rehab-blue); color:#fff; }
  .rehab-role-text b { display:block; font-size:13px; line-height:1.15; }
  .rehab-role-text span { display:block; color:var(--rehab-muted); font-size:10.5px; line-height:1.15; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:120px; }
  .rehab-field { margin-bottom:15px; }
  .rehab-input {
    height:46px; display:flex; align-items:center; gap:9px; padding:0 12px;
    background:var(--rehab-bg-soft); border:1px solid var(--rehab-line); border-radius:11px; transition:.16s;
  }
  .rehab-input:focus-within { background:var(--rehab-card); border-color:var(--rehab-blue); box-shadow:0 0 0 3px rgba(37,110,217,.13); }
  .rehab-input .rehab-icon { width:17px; height:17px; color:var(--rehab-muted); }
  .rehab-input input { flex:1; width:100%; height:100%; border:0; outline:0; background:transparent; color:var(--rehab-primary); font:500 14.5px var(--rehab-ui); }
  .rehab-input input::placeholder { color:var(--rehab-muted); }
  .rehab-eye { border:0; background:transparent; color:var(--rehab-muted); cursor:pointer; display:grid; place-items:center; padding:4px; }
  .rehab-primary-btn {
    width:100%; height:48px; border:0; border-radius:12px; cursor:pointer;
    display:inline-flex; align-items:center; justify-content:center; gap:9px;
    background:linear-gradient(145deg, var(--rehab-blue), var(--rehab-blue-strong)); color:#fff;
    font:800 14.5px var(--rehab-ui); box-shadow:0 8px 20px rgba(37,110,217,.26);
  }
  .rehab-primary-btn:hover { transform:translateY(-1px); box-shadow:0 12px 26px rgba(37,110,217,.30); }
  .rehab-auth-foot { margin-top:16px; text-align:center; color:var(--rehab-muted); font-size:12.5px; }
  .rehab-auth-foot button { border:0; background:transparent; color:var(--rehab-blue); font-weight:800; cursor:pointer; padding:0; }
  .rehab-demo-strip { margin-top:20px; border-top:1px dashed var(--rehab-line); padding-top:16px; }
  .rehab-demo-title { text-align:center; text-transform:uppercase; color:var(--rehab-muted); letter-spacing:.4px; font:800 11px var(--rehab-ui); margin-bottom:10px; }
  .rehab-demo-btns { display:flex; flex-wrap:wrap; gap:7px; justify-content:center; }
  .rehab-demo-btns button {
    display:inline-flex; align-items:center; gap:6px; border:1px solid var(--rehab-line);
    background:var(--rehab-bg-soft); color:var(--rehab-secondary); border-radius:999px;
    padding:6px 11px; font:800 11.5px var(--rehab-ui); cursor:pointer;
  }
  .rehab-demo-btns button:hover { border-color:var(--rehab-blue); color:var(--rehab-blue); transform:translateY(-1px); }
  .rehab-notice {
    margin:0 0 14px; padding:10px 12px; border-radius:8px; border:1px solid var(--rehab-line);
    background:var(--rehab-bg-soft); color:var(--rehab-secondary); font-size:12.5px; line-height:1.35;
  }
  .rehab-notice.error { border-color:rgba(220,38,38,.24); background:rgba(220,38,38,.08); color:var(--rehab-danger); }
  .rehab-notice.success { border-color:rgba(5,150,105,.24); background:rgba(5,150,105,.08); color:var(--rehab-success); }
  html[data-rehab-theme="dark"] .rehab-auth-root,
  html[data-rehab-theme="dark"] .rehab-auth-wrap { color-scheme:dark; }
  @media (max-width: 980px) {
    .rehab-auth-root { top:var(--rehab-topbar-h); }
    .rehab-auth-wrap { grid-template-columns:1fr; padding:22px 20px 40px; gap:18px; }
    .rehab-auth-hero { min-height:auto; gap:18px; }
    .rehab-auth-eyebrow, .rehab-auth-hero p, .rehab-auth-stats { display:none; }
    .rehab-auth-hero h1 { font-size:clamp(32px,12vw,48px); max-width:9.4em; }
    .rehab-pose { position:relative; right:auto; bottom:auto; width:154px; align-self:center; margin:4px auto -2px; order:5; }
    .rehab-auth-panel { align-items:flex-start; }
    .rehab-auth-card { max-width:430px; padding:28px 20px; }
  }
  @media (max-width: 520px) {
    .rehab-auth-wrap { min-height:calc(100vh - var(--rehab-topbar-h)); padding:16px 20px 34px; align-items:start; }
    .rehab-auth-hero { display:none; }
    .rehab-auth-card { border-radius:16px; padding:24px 18px; margin-top:12px; }
    .rehab-role-grid { grid-template-columns:1fr; }
    .rehab-demo-btns button { font-size:11px; padding:6px 10px; }
  }
  `;

  const roles = {
    patient:{label:"Bệnh nhân", value:"Bệnh nhân", icon:"i-heart", desc:"Tập luyện & theo dõi", acc:"bn01"},
    doctor_ktv:{label:"Bác sĩ / KTV", value:"Bác sĩ / KTV PHCN", icon:"i-stetho", desc:"Đánh giá & soát kỹ thuật", acc:"bsi01"},
    researcher:{label:"NCV", value:"Nghiên cứu viên", icon:"i-micro", desc:"Phân tích & hiệu chỉnh AI", acc:"ncv01"},
    admin:{label:"Quản trị", value:"Quản trị viên", icon:"i-cog", desc:"Vận hành hệ thống", acc:"admin"},
  };

  let mode = "login";
  let pickedRole = "doctor_ktv";

  function doc() {
    try { return window.parent.document; } catch (_) { return document; }
  }

  function ensureStyle() {
    const d = doc();
    if (!d.getElementById("rehab-auth-style")) {
      const style = d.createElement("style");
      style.id = "rehab-auth-style";
      style.textContent = css;
      d.head.appendChild(style);
    }
  }

  function icon(id) {
    return `<svg class="rehab-icon" aria-hidden="true"><use href="#${id}"></use></svg>`;
  }

  function poseMarkup() {
    return `<div class="rehab-pose" aria-hidden="true">
      <svg viewBox="0 0 240 260">
        <line x1="120" y1="92" x2="210" y2="92" stroke="var(--rehab-muted)" stroke-width="2" stroke-dasharray="5 6" opacity=".5"/>
        <path class="arc" d="M150 92 A30 30 0 0 0 132 64"/>
        <text x="158" y="80" fill="#7773FF" font-family="var(--rehab-mono)" font-size="13" font-weight="700">128°</text>
        <circle cx="120" cy="40" r="16" class="joint"/>
        <line x1="120" y1="56" x2="120" y2="150" class="bone"/>
        <line x1="120" y1="92" x2="86" y2="138" class="bone dim"/>
        <line x1="86" y1="138" x2="74" y2="178" class="bone dim"/>
        <circle cx="86" cy="138" r="6" class="joint dim"/>
        <g id="rehabPoseArm">
          <line x1="120" y1="92" x2="170" y2="118" class="bone"/>
          <line x1="170" y1="118" x2="206" y2="132" class="bone"/>
          <circle cx="170" cy="118" r="6" class="joint"/>
          <circle cx="206" cy="132" r="5.5" class="joint"/>
        </g>
        <circle cx="120" cy="92" r="7" class="joint"/>
        <line x1="120" y1="150" x2="100" y2="214" class="bone"/>
        <line x1="120" y1="150" x2="140" y2="214" class="bone"/>
        <circle cx="120" cy="150" r="6" class="joint"/>
        <circle cx="100" cy="214" r="5.5" class="joint"/>
        <circle cx="140" cy="214" r="5.5" class="joint"/>
      </svg>
    </div>`;
  }

  function field(name, label, type, placeholder, iconId, value) {
    return `<div class="rehab-field" data-field="${name}">
      <label for="rehab-${name}">${label}</label>
      <div class="rehab-input">
        ${icon(iconId)}
        <input id="rehab-${name}" name="${name}" type="${type}" placeholder="${placeholder || ""}" value="${value || ""}" autocomplete="${type === "password" ? "current-password" : "off"}">
        ${type === "password" ? `<button class="rehab-eye" type="button" data-eye="${name}">${icon("i-eye")}</button>` : ""}
      </div>
    </div>`;
  }

  function roleGrid() {
    const order = ["doctor_ktv", "researcher", "patient", "admin"];
    return `<div class="rehab-role-label">Bạn đăng ký với tư cách</div>
      <div class="rehab-role-grid">
      ${order.map((key) => {
        const role = roles[key];
        return `<button type="button" class="rehab-role-opt ${key === "admin" ? "full" : ""} ${key === pickedRole ? "on" : ""}" data-role="${key}">
          <span class="rehab-role-icon">${icon(role.icon)}</span>
          <span class="rehab-role-text"><b>${role.label}</b><span>${role.desc}</span></span>
        </button>`;
      }).join("")}
      </div>`;
  }

  function mount(payload, sendEvent, helpers) {
    ensureStyle();
    const d = doc();
    let root = d.getElementById("rehab-auth-root");
    if ((payload.mode || "auth") !== "auth") {
      if (root) root.remove();
      return;
    }
    if (!root) {
      root = d.createElement("section");
      root.id = "rehab-auth-root";
      root.className = "rehab-auth-root";
      d.body.appendChild(root);
    }
    const notice = payload.notice || {};
    const isRegister = mode === "register";
    root.innerHTML = `<div class="rehab-auth-wrap">
      <div class="rehab-auth-hero">
        <span class="rehab-auth-eyebrow">${icon("i-shield")} Clinical-Grade · Giám sát từ xa bằng Thị giác máy tính</span>
        <h1>Giám sát tập <em>phục hồi chức năng</em> bằng AI, ngay tại nhà.</h1>
        <p>Bệnh nhân khai báo triệu chứng (VAS) → AI phân tích khung xương & góc khớp theo thời gian thực → Chuyên gia đối chiếu và đưa ra phác đồ. Một luồng lâm sàng khép kín.</p>
        <div class="rehab-auth-stats">
          <div class="rehab-auth-stat"><b>33</b><span>điểm khung xương / khung hình</span></div>
          <div class="rehab-auth-stat"><b>±15°</b><span>sai số mục tiêu giai đoạn 3</span></div>
          <div class="rehab-auth-stat"><b>5</b><span>vai trò người dùng</span></div>
        </div>
        ${poseMarkup()}
      </div>
      <div class="rehab-auth-panel">
        <form class="rehab-auth-card" id="rehab-auth-form">
          <h2>${isRegister ? "Tạo tài khoản mới" : "Đăng nhập hệ thống"}</h2>
          <p class="rehab-auth-sub">${isRegister ? "Tài khoản KTV / Bác sĩ / NCV cần Quản trị viên phê duyệt trước khi kích hoạt." : "Truy cập bảng điều khiển theo vai trò của bạn."}</p>
          <div class="rehab-seg">
            <button type="button" class="${!isRegister ? "on" : ""}" data-mode="login">Đăng nhập</button>
            <button type="button" class="${isRegister ? "on" : ""}" data-mode="register">Đăng ký</button>
          </div>
          ${notice.message ? `<div class="rehab-notice ${notice.kind || ""}">${helpers.esc(notice.message)}</div>` : ""}
          ${isRegister ? roleGrid() : ""}
          ${isRegister ? field("fullName", "Họ và tên", "text", "VD: Nguyễn Văn A", "i-users", "") : ""}
          ${field("username", isRegister ? "Tên đăng nhập" : "Tài khoản", "text", isRegister ? "Chọn tên tài khoản" : "bsi01", "i-user", isRegister ? "" : "bsi01")}
          ${isRegister ? field("email", "Email / Số điện thoại", "text", "email@huph.edu.vn", "i-mail", "") : ""}
          ${field("password", "Mật khẩu", "password", "••••••••", "i-lock", "")}
          ${isRegister ? field("password2", "Nhập lại mật khẩu", "password", "••••••••", "i-lock", "") : ""}
          <button class="rehab-primary-btn" type="submit">${isRegister ? "Đăng ký tài khoản" : "Đăng nhập"} ${icon("i-arrow")}</button>
          ${!isRegister ? `<div class="rehab-auth-foot">Quên mật khẩu? <button type="button" data-forgot>Khôi phục tại đây</button></div>` : ""}
          <div class="rehab-demo-strip">
            <div class="rehab-demo-title">Xem nhanh demo theo vai trò</div>
            <div class="rehab-demo-btns">
              ${Object.entries(roles).map(([key, role]) => `<button type="button" data-demo="${key}">${icon(role.icon)}${role.label}</button>`).join("")}
            </div>
          </div>
        </form>
      </div>
    </div>`;

    root.querySelectorAll("[data-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        mode = btn.getAttribute("data-mode") || "login";
        mount(payload, sendEvent, helpers);
      });
    });
    root.querySelectorAll("[data-role]").forEach((btn) => {
      btn.addEventListener("click", () => {
        pickedRole = btn.getAttribute("data-role") || "doctor_ktv";
        mount(payload, sendEvent, helpers);
      });
    });
    root.querySelectorAll("[data-eye]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const input = root.querySelector(`#rehab-${btn.getAttribute("data-eye")}`);
        if (input) input.type = input.type === "password" ? "text" : "password";
      });
    });
    const forgot = root.querySelector("[data-forgot]");
    if (forgot) {
      forgot.addEventListener("click", () => sendEvent({ type: "forgot_password" }));
    }
    root.querySelectorAll("[data-demo]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const role = roles[btn.getAttribute("data-demo") || "doctor_ktv"];
        sendEvent({ type: "demo_login", role: role.value });
      });
    });
    const form = root.querySelector("#rehab-auth-form");
    if (form) {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        const data = new FormData(form);
        if (mode === "register") {
          sendEvent({
            type: "register",
            role: roles[pickedRole].value,
            full_name: data.get("fullName") || "",
            username: data.get("username") || "",
            email: data.get("email") || "",
            password: data.get("password") || "",
            password2: data.get("password2") || "",
          });
        } else {
          sendEvent({
            type: "login",
            username: data.get("username") || "",
            password: data.get("password") || "",
          });
        }
      });
    }
  }

  window.RehabAuthUI = { mount };
})();
