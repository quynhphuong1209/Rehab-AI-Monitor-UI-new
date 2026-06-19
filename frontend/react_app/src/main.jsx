import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

const roots = new WeakMap();

function norm(value) {
  return String(value || "").toLowerCase();
}

function roleKey(payload) {
  const role = norm(payload?.role || payload?.user?.role);
  if (role.includes("quản") || role.includes("quan")) return "admin";
  if (role.includes("nghiên") || role.includes("nghien") || role.includes("ncv")) return "researcher";
  if (role.includes("bác") || role.includes("bac") || role.includes("ktv")) return "doctor";
  return "patient";
}

function appNotice(payload) {
  return payload?.notices?.app || null;
}

function Notice({ notice }) {
  if (!notice?.message) return null;
  return <div className={`rehab-react-notice ${notice.type === "error" ? "error" : ""}`}>{notice.message}</div>;
}

function Title({ eyebrow, title, subtitle, action }) {
  return (
    <section className="rehab-react-title">
      <div>
        {eyebrow ? <span className="rehab-role-eyebrow">{eyebrow}</span> : null}
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {action ? <div>{action}</div> : null}
    </section>
  );
}

function Metrics({ items }) {
  return (
    <div className="rehab-react-grid">
      {items.map((item) => (
        <article className="rehab-react-card rehab-react-metric" key={item.label}>
          <b>{item.value}</b>
          <span>{item.label}</span>
          {item.sub ? <small>{item.sub}</small> : null}
        </article>
      ))}
    </div>
  );
}

function SymptomsTable({ symptoms }) {
  const rows = symptoms || [];
  if (!rows.length) {
    return <div className="rehab-react-list-item"><b>Chưa có khai báo</b><span>Form bên trái sẽ lưu vào patient_symptoms.json.</span></div>;
  }
  return (
    <table className="rehab-react-table">
      <thead>
        <tr><th>Ngày</th><th>VAS</th><th>Vị trí</th><th>Mô tả</th><th>Bài tập</th></tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr key={`${row.created_at || row.time || idx}`}>
            <td>{row.date || row.time || "N/A"}</td>
            <td>{row.vas ?? "N/A"}/10</td>
            <td>{row.pain_location || "Chưa ghi"}</td>
            <td>{row.symptoms || "Chưa ghi"}</td>
            <td>{row.exercise || "Chưa chọn"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PatientApp({ payload, sendEvent }) {
  const user = payload.user || {};
  const symptoms = payload.patient?.symptoms || [];
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({
    vas: 3,
    pain_location: "",
    exercise: "Bài tập con lắc Codman",
    date: today,
    symptoms: "",
  });
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const submit = (event) => {
    event.preventDefault();
    sendEvent({ type: "patient_create_symptom", payload: form });
  };
  return (
    <main className="rehab-react-shell">
      <Title
        eyebrow="Patient workspace"
        title="Theo dõi phục hồi"
        subtitle={`Xin chào ${user.full_name || user.username || "bệnh nhân"}. Khai báo triệu chứng và theo dõi lịch sử tập luyện trong một giao diện.`}
      />
      <Notice notice={appNotice(payload)} />
      <Metrics items={[
        { label: "Khai báo gần nhất", value: symptoms.length ? `${symptoms[0].vas ?? "N/A"}/10` : "N/A", sub: "VAS hiện tại" },
        { label: "Tổng khai báo", value: symptoms.length, sub: "Theo tài khoản đang đăng nhập" },
        { label: "Upload video", value: "Soon", sub: "Slice kế tiếp" },
      ]} />
      <section className="rehab-react-panel">
        <article className="rehab-react-card">
          <h2>Khai báo triệu chứng</h2>
          <form className="rehab-react-form" onSubmit={submit}>
            <div className="rehab-react-field">
              <label>Mức độ đau VAS: {form.vas}/10</label>
              <input type="range" min="0" max="10" value={form.vas} onChange={(e) => update("vas", e.target.value)} />
            </div>
            <div className="rehab-react-field">
              <label>Vị trí đau</label>
              <input value={form.pain_location} onChange={(e) => update("pain_location", e.target.value)} placeholder="VD: Vai phải, bả vai, khuỷu..." />
            </div>
            <div className="rehab-react-field">
              <label>Bài tập</label>
              <select value={form.exercise} onChange={(e) => update("exercise", e.target.value)}>
                <option>Bài tập con lắc Codman</option>
                <option>Bài tập với gậy (Pulley Exercise)</option>
                <option>Bài tập dây kháng lực</option>
                <option>Khác</option>
              </select>
            </div>
            <div className="rehab-react-field">
              <label>Ngày khai báo</label>
              <input type="date" value={form.date} onChange={(e) => update("date", e.target.value)} />
            </div>
            <div className="rehab-react-field">
              <label>Mô tả triệu chứng</label>
              <textarea value={form.symptoms} onChange={(e) => update("symptoms", e.target.value)} placeholder="VD: Đau khi giơ tay quá đầu, cứng vai buổi sáng..." />
            </div>
            <button className="rehab-react-button" type="submit">Gửi khai báo triệu chứng</button>
          </form>
        </article>
        <article className="rehab-react-card">
          <h2>Lịch sử khai báo</h2>
          <SymptomsTable symptoms={symptoms} />
        </article>
      </section>
    </main>
  );
}

function DoctorKtvApp({ payload }) {
  const stats = payload.sideStats || {};
  return (
    <main className="rehab-react-shell">
      <Title eyebrow="Clinical workspace" title="Danh sách bệnh nhân" subtitle="Bảng mềm cho hàng chờ đánh giá, giữ backend đánh giá Streamlit ở lớp dưới trong giai đoạn chuyển đổi." />
      <Metrics items={[
        { label: "Tổng bệnh nhân", value: stats.patients ?? 0, sub: "Theo video hiện có" },
        { label: "Chờ đánh giá", value: stats.pending ?? 0, sub: "Lấy từ đánh giá thật" },
        { label: "Phiên tập", value: stats.sessions ?? 0, sub: "Video trong hệ thống" },
      ]} />
      <section className="rehab-react-card">
        <h2>Hàng chờ đánh giá</h2>
        <div className="rehab-react-list">
          <div className="rehab-react-list-item"><b>Form đánh giá lâm sàng</b><span>Slice sau sẽ migrate từ Streamlit sang React.</span></div>
          <div className="rehab-react-list-item"><b>Nhật ký đánh giá</b><span>Giữ logic CSV/xóa/ghi chú hiện có.</span></div>
        </div>
      </section>
    </main>
  );
}

function ResearcherApp({ payload }) {
  const stats = payload.sideStats || {};
  return (
    <main className="rehab-react-shell">
      <Title eyebrow="Research workspace" title="Quản lý Dataset" subtitle="Không gian NCV cho dataset, video nghiên cứu và tiến trình AI/MediaPipe." />
      <Metrics items={[
        { label: "Video nghiên cứu", value: stats.total_videos ?? stats.videos ?? 0, sub: "Tổng dữ liệu" },
        { label: "Đã có AI", value: stats.ai_done ?? 0, sub: "Kết quả phân tích" },
        { label: "Điểm khung xương", value: stats.keypoints ?? 33, sub: "Keypoints/khung hình" },
      ]} />
      <section className="rehab-react-card">
        <h2>Tiến trình migration AI jobs</h2>
        <div className="rehab-react-list">
          <div className="rehab-react-list-item"><b>Start/status/cancel analysis</b><span>Chuẩn bị API job ở slice sau.</span></div>
          <div className="rehab-react-list-item"><b>Frames, chart, report</b><span>Sẽ nối media endpoint an toàn.</span></div>
        </div>
      </section>
    </main>
  );
}

function AdminApp({ payload }) {
  const stats = payload.sideStats || {};
  return (
    <main className="rehab-react-shell">
      <Title eyebrow="Admin workspace" title="Bảng điều khiển hệ thống" subtitle="Quản lý tài khoản, dữ liệu và audit log bằng layout card/table mềm." />
      <Metrics items={[
        { label: "Tài khoản", value: stats.accounts ?? 0, sub: "Users JSON" },
        { label: "Video", value: stats.videos ?? 0, sub: "Video list" },
        { label: "Đánh giá", value: stats.evals ?? 0, sub: "Doctor evaluations" },
      ]} />
      <section className="rehab-react-card">
        <h2>Admin panel</h2>
        <div className="rehab-react-list">
          <div className="rehab-react-list-item"><b>Tạo/xóa user</b><span>Giữ Streamlit nghiệp vụ cũ trong phase này.</span></div>
          <div className="rehab-react-list-item"><b>Audit/export/reset</b><span>Đưa sang API ở các slice kế tiếp.</span></div>
        </div>
      </section>
    </main>
  );
}

function App({ payload, sendEvent }) {
  const key = roleKey(payload);
  if (key === "admin") return <AdminApp payload={payload} sendEvent={sendEvent} />;
  if (key === "researcher") return <ResearcherApp payload={payload} sendEvent={sendEvent} />;
  if (key === "doctor") return <DoctorKtvApp payload={payload} sendEvent={sendEvent} />;
  return <PatientApp payload={payload} sendEvent={sendEvent} />;
}

function mount(container, payload, sendEvent) {
  if (!container) return;
  let root = roots.get(container);
  if (!root) {
    root = createRoot(container);
    roots.set(container, root);
  }
  root.render(<App payload={payload || {}} sendEvent={sendEvent || (() => {})} />);
}

function unmount(container) {
  const root = container ? roots.get(container) : null;
  if (root) {
    root.unmount();
    roots.delete(container);
  }
}

window.RehabReactApp = { mount, unmount };
