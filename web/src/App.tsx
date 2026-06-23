import {
  Activity,
  AlertCircle,
  BarChart3,
  ChevronRight,
  ClipboardList,
  Database,
  Download,
  Eye,
  EyeOff,
  FileText,
  FlaskConical,
  HeartPulse,
  KeyRound,
  Link as LinkIcon,
  LayoutDashboard,
  Lock,
  LogOut,
  Mail,
  PanelLeftClose,
  PanelLeftOpen,
  Microscope,
  Moon,
  Settings,
  PlayCircle,
  RefreshCw,
  Search,
  Shield,
  Stethoscope,
  Sun,
  Target,
  Upload,
  UserRound,
  UserPlus,
  Users,
  Video,
} from "lucide-react";
import { type FormEvent, type ReactNode, useEffect, useMemo, useRef, useState, useTransition } from "react";
import { createPortal } from "react-dom";

import { api, ApiError } from "./api";
import type {
  AnalysisJob,
  AnalysisJobOptions,
  AuthResponse,
  BoxPlotItem,
  DashboardPayload,
  Metrics,
  RoleKey,
  User,
  VideoDetailPayload,
} from "./types";

const tokenKey = "rehab_api_token";
const themeKey = "rehab_ui_theme";

type ThemeMode = "light" | "dark";

const roles = [
  "Quản trị viên",
  "Bác sĩ / KTV PHCN",
  "Nghiên cứu viên",
  "Bệnh nhân",
];

const roleNames: Record<RoleKey, string> = {
  admin: "Quản trị viên",
  doctor_ktv: "Bác sĩ / KTV PHCN",
  researcher: "Nghiên cứu viên",
  patient: "Bệnh nhân",
};

const exerciseGuides = [
  {
    key: "codman",
    name: "Bài tập con lắc Codman",
    icon: "Codman",
    youtube: "https://youtu.be/a4eCRWuqO40",
    duration: 30,
    reps: 10,
    description: "Bài tập dao động tay thụ động theo quán tính, giúp thả lỏng khớp vai, giảm đau và chống dính khớp.",
    steps: [
      "Đứng thẳng, cúi người về phía trước 30-45 độ.",
      "Tay bệnh thả lỏng hoàn toàn, tay lành chống lên bàn hoặc ghế để giữ thăng bằng.",
      "Đung đưa tay nhẹ theo chiều trước-sau, sang ngang và vòng tròn.",
      "Mỗi động tác 10 lần, nghỉ 5-10 giây; thở ra khi đưa tay lên, hít vào khi hạ tay.",
    ],
    benefits: [
      "Giảm đau khớp vai sau chấn thương hoặc viêm quanh khớp.",
      "Tăng tuần hoàn máu tại chỗ và chống dính khớp.",
      "Duy trì tầm vận động khớp vai và giảm co cứng cơ quanh khớp.",
    ],
    cautions: [
      "Không tập khi đau vai cấp tính chưa rõ nguyên nhân.",
      "Tránh động tác quá mạnh hoặc quá nhanh.",
      "Dừng tập nếu đau tăng hoặc xuất hiện đau mới.",
    ],
  },
  {
    key: "pulley",
    name: "Bài tập với gậy (Pulley Exercise)",
    icon: "Gậy",
    youtube: "https://www.youtube.com/watch?v=s2O8WHT5o2k",
    duration: 45,
    reps: 12,
    description: "Sử dụng gậy hoặc ròng rọc hỗ trợ nâng tay và xoay vai bị hạn chế vận động.",
    steps: [
      "Cầm gậy bằng hai tay, tay lành cầm một đầu, tay bệnh cầm đầu kia.",
      "Tay lành dùng lực đẩy gậy lên cao, kéo tay bệnh theo biên độ trong video mẫu.",
      "Giữ 5-10 giây ở tư thế cao nhất rồi hạ từ từ.",
      "Thực hiện nâng trước, xoay ngoài, xoay trong; không nín thở trong khi tập.",
    ],
    benefits: [
      "Cải thiện tầm vận động khớp vai chủ động và thụ động.",
      "Giảm chênh lệch vận động giữa hai tay.",
      "Phục hồi khả năng với tay và nâng vật trên cao.",
    ],
    cautions: [
      "Không kéo gậy quá tầm chịu đựng.",
      "Tránh thực hiện khi đau vai cấp hoặc VAS > 5.",
      "Theo dõi dấu hiệu tê bì tay hoặc đau lan.",
    ],
  },
  {
    key: "theraband",
    name: "Bài tập với dây kháng lực (Theraband Exercise)",
    icon: "Dây",
    youtube: "https://www.youtube.com/watch?v=njDHDnZ6lis",
    duration: 40,
    reps: 15,
    description: "Tăng cường sức mạnh cơ chóp xoay và cơ quanh khớp vai bằng dây thun kháng lực.",
    steps: [
      "Bắt đầu với dây kháng lực thấp nhất, thường là màu vàng hoặc đỏ.",
      "Xoay vai ngoài: gập khuỷu 90 độ, xoay cẳng tay ra ngoài theo mẫu.",
      "Xoay vai trong: kéo dây vào trong, áp sát tay vào bụng.",
      "Dang vai hoặc gập vai theo video hướng dẫn, mỗi động tác 10-15 lần x 3 hiệp.",
    ],
    benefits: [
      "Tăng sức mạnh và sức bền của cơ chóp xoay.",
      "Ổn định khớp vai trong hoạt động hằng ngày.",
      "Duy trì thành quả sau điều trị dài hạn.",
    ],
    cautions: [
      "Không tập khi đau cấp hoặc viêm khớp vai đang tiến triển.",
      "Theo dõi đau kéo dài hơn 24 giờ sau tập.",
      "Kiểm soát cả hai thì, không giật dây quá nhanh.",
    ],
  },
];

const loginRoleHints = [
  {
    key: "patient",
    label: "Bệnh nhân",
    text: "Đăng nhập bằng tài khoản bệnh nhân đã tạo; nếu chưa có tài khoản thì dùng Đăng ký.",
  },
  {
    key: "doctor",
    label: "Bác sĩ / KTV",
    text: "Dùng tài khoản đã được quản trị viên cấp để xem video, phiếu đánh giá và lịch nhắc.",
  },
  {
    key: "researcher",
    label: "NCV",
    text: "Dùng tài khoản nghiên cứu viên để xem dữ liệu NCKH, frame gallery và phân tích AI.",
  },
  {
    key: "admin",
    label: "QTV",
    text: "Dùng tài khoản quản trị viên để quản lý người dùng, dữ liệu và điều phối hệ thống.",
  },
];

type ViewKey =
  | "home"
  | "admin_video"
  | "admin_research"
  | "patient_results"
  | "patient_schedule"
  | "evaluation_forms"
  | "research_results"
  | "research_analysis"
  | "admin_panel"
  | "admin_info"
  | "team"
  | "info"
  | "contact"
  | "feedback";

function asText(value: unknown) {
  if (value === null || value === undefined || value === "") return "N/A";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function foldedText(value: unknown) {
  return asText(value)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\u0111/g, "d");
}

function compactText(value: unknown, max = 110) {
  const text = asText(value);
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function isActiveJobStatus(status: unknown) {
  return ["queued", "processing", "ready_for_ai_worker"].includes(String(status || "").toLowerCase());
}

function roleClass(role: string) {
  const roleText = role.toLowerCase();
  if (roleText.includes("quản") || roleText.includes("admin")) return "admin";
  if (roleText.includes("nghiên")) return "researcher";
  if (roleText.includes("bác") || roleText.includes("ktv")) return "doctor";
  return "patient";
}

function roleIconFor(roleKeyValue: RoleKey): typeof Activity {
  if (roleKeyValue === "admin") return Settings;
  if (roleKeyValue === "researcher") return Microscope;
  if (roleKeyValue === "doctor_ktv") return Stethoscope;
  return HeartPulse;
}

function avatarInitials(name: string, fallback = "RA") {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return fallback;
  if (parts.length === 1) return Array.from(parts[0]).slice(0, 2).join("").toUpperCase();
  return `${Array.from(parts[0])[0] || ""}${Array.from(parts[parts.length - 1])[0] || ""}`.toUpperCase();
}

function roleTabs(roleKeyValue: RoleKey, _hasDoctorVideoOutput: boolean) {
  if (roleKeyValue === "admin") {
    return [
      { key: "home" as ViewKey, label: "TRANG CHỦ", icon: LayoutDashboard },
      { key: "admin_panel" as ViewKey, label: "QUẢN TRỊ VIÊN", icon: Settings },
      { key: "evaluation_forms" as ViewKey, label: "PHIẾU ĐÁNH GIÁ", icon: ClipboardList },
      { key: "admin_research" as ViewKey, label: "DỮ LIỆU NCKH", icon: FlaskConical },
      { key: "admin_info" as ViewKey, label: "THÔNG TIN TỔNG HỢP", icon: FileText },
      { key: "team" as ViewKey, label: "HỒ SƠ ĐỀ TÀI", icon: Users },
      { key: "feedback" as ViewKey, label: "PHẢN HỒI", icon: ClipboardList },
    ];
  }
  if (roleKeyValue === "doctor_ktv") {
    return [
      { key: "home" as ViewKey, label: "TRANG CHỦ", icon: LayoutDashboard },
      { key: "evaluation_forms" as ViewKey, label: "PHIẾU ĐÁNH GIÁ", icon: FileText },
      { key: "patient_schedule" as ViewKey, label: "LỊCH NHẮC NHỞ", icon: Activity },
      { key: "info" as ViewKey, label: "THÔNG TIN TỔNG HỢP", icon: FileText },
      { key: "team" as ViewKey, label: "HỒ SƠ ĐỀ TÀI", icon: Users },
      { key: "contact" as ViewKey, label: "LIÊN HỆ", icon: Mail },
      { key: "feedback" as ViewKey, label: "PHẢN HỒI", icon: ClipboardList },
    ];
  }
  if (roleKeyValue === "patient") {
    return [
      { key: "home" as ViewKey, label: "TRANG CHỦ", icon: LayoutDashboard },
      { key: "patient_results" as ViewKey, label: "KẾT QUẢ ĐÁNH GIÁ", icon: BarChart3 },
      { key: "patient_schedule" as ViewKey, label: "LỊCH NHẮC NHỞ", icon: Activity },
      { key: "info" as ViewKey, label: "TRANG THÔNG TIN NGHIÊN CỨU", icon: FileText },
      { key: "contact" as ViewKey, label: "LIÊN HỆ", icon: Mail },
      { key: "feedback" as ViewKey, label: "PHẢN HỒI", icon: ClipboardList },
    ];
  }
  return [
    { key: "home" as ViewKey, label: "TRANG CHỦ", icon: LayoutDashboard },
    { key: "evaluation_forms" as ViewKey, label: "PHIẾU ĐÁNH GIÁ", icon: ClipboardList },
    { key: "research_analysis" as ViewKey, label: "PHÂN TÍCH & TRÍCH XUẤT", icon: FlaskConical },
    { key: "admin_research" as ViewKey, label: "DỮ LIỆU NCKH", icon: Database },
    { key: "info" as ViewKey, label: "THÔNG TIN TỔNG HỢP", icon: FileText },
    { key: "team" as ViewKey, label: "HỒ SƠ ĐỀ TÀI", icon: Users },
    { key: "feedback" as ViewKey, label: "PHẢN HỒI", icon: ClipboardList },
  ];
}

function defaultTabForRole(roleKeyValue: RoleKey): ViewKey {
  return "home";
}

function isResultTab(tab: ViewKey) {
  return tab === "admin_video" || tab === "patient_results" || tab === "research_results" || tab === "research_analysis";
}

function mediaUrl(path: string) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  const separator = path.includes("?") ? "&" : "?";
  return `${api.baseUrl}${path}${separator}v=${encodeURIComponent(path)}`;
}

function browserDownload(url: string, filename?: string) {
  if (!url) return;
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename || "";
  anchor.rel = "noreferrer";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

function PoseGraphic() {
  return (
    <div className="auth-pose" aria-hidden="true">
      <svg viewBox="0 0 240 260">
        <line x1="120" y1="92" x2="210" y2="92" className="pose-guide" />
        <path className="pose-arc" d="M150 92 A30 30 0 0 0 132 64" />
        <text x="158" y="80" className="pose-text">
          128°
        </text>
        <circle cx="120" cy="40" r="16" className="pose-joint" />
        <line x1="120" y1="56" x2="120" y2="150" className="pose-bone" />
        <line x1="120" y1="92" x2="86" y2="138" className="pose-bone dim" />
        <line x1="86" y1="138" x2="74" y2="178" className="pose-bone dim" />
        <circle cx="86" cy="138" r="6" className="pose-joint dim" />
        <g className="pose-arm">
          <line x1="120" y1="92" x2="170" y2="118" className="pose-bone" />
          <line x1="170" y1="118" x2="206" y2="132" className="pose-bone" />
          <circle cx="170" cy="118" r="6" className="pose-joint" />
          <circle cx="206" cy="132" r="5.5" className="pose-joint" />
        </g>
        <circle cx="120" cy="92" r="7" className="pose-joint" />
        <line x1="120" y1="150" x2="100" y2="214" className="pose-bone" />
        <line x1="120" y1="150" x2="140" y2="214" className="pose-bone" />
        <circle cx="120" cy="150" r="6" className="pose-joint" />
        <circle cx="100" cy="214" r="5.5" className="pose-joint" />
        <circle cx="140" cy="214" r="5.5" className="pose-joint" />
      </svg>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  hint: string;
}) {
  return (
    <article className="stat-card">
      <div className="stat-icon">
        <Icon size={20} aria-hidden="true" />
      </div>
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
        <small>{hint}</small>
      </div>
    </article>
  );
}

function DataTable({
  rows,
  columns,
  empty,
}: {
  rows: Record<string, unknown>[];
  columns: { key: string; label: string; wide?: boolean }[];
  empty: string;
}) {
  if (!rows.length) {
    return <div className="empty-state">{empty}</div>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={column.wide ? "wide" : undefined}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.username || row.video_name || row.time || index}`}>
              {columns.map((column) => (
                <td key={column.key} className={column.wide ? "wide" : undefined}>
                  {compactText(row[column.key], column.wide ? 150 : 72)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatBytes(value: unknown) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) return "";
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function ArtifactExportPanel({
  token,
  identifier,
  detail,
  onSaved,
  compact = false,
}: {
  token: string;
  identifier: string | number;
  detail: VideoDetailPayload;
  onSaved: () => void;
  compact?: boolean;
}) {
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [links, setLinks] = useState<Record<string, { url: string; filename: string; size: number }>>({});
  const codmanGroups = (detail.frame_groups || []).filter((group) => ["g1", "g2", "g3"].includes(group.key) && group.total > 0);
  const phaseButtons = [{ key: "all", label: "Tất cả" }, ...codmanGroups.map((group) => ({ key: group.key, label: group.label }))];

  async function prepare(kind: "video" | "frames", phase: string) {
    const key = `${kind}-${phase}`;
    setBusy(key);
    setMessage("");
    try {
      const result = await api.prepareVideoExport(token, identifier, kind, phase, true);
      setLinks((current) => ({
        ...current,
        [key]: { url: result.url, filename: result.filename, size: result.size },
      }));
      browserDownload(mediaUrl(result.url), result.filename);
      const datasetNote = result.dataset_path ? ` Dataset: ${result.dataset_path}.` : "";
      setMessage(
        kind === "video"
          ? `Đã lưu video vào database/dataset, gửi cho bệnh nhân/Bác sĩ-KTV và tải về máy.${datasetNote}`
          : `Đã lưu ZIP frames kèm CSV/JSON vào database/dataset, gửi cho bệnh nhân/Bác sĩ-KTV và tải về máy.${datasetNote}`,
      );
      window.setTimeout(onSaved, 350);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không chuẩn bị được file lưu/tải.");
    } finally {
      setBusy("");
    }
  }

  async function saveBundle() {
    setBusy("bundle");
    setMessage("");
    try {
      const result = await api.saveLatestVideoBundle(token);
      const bundle = result.bundle || {};
      setMessage(`Đã lưu bundle 8 video vào ${result.path} và đồng bộ cho bệnh nhân/Bác sĩ-KTV. Cập nhật: ${asText(bundle.updated_at || "vừa xong")}.`);
      window.setTimeout(onSaved, 350);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không lưu được bundle 8 video.");
    } finally {
      setBusy("");
    }
  }

  return (
    <div className={compact ? "artifact-export-panel compact" : "artifact-export-panel"}>
      <div>
        <button className="bundle-save-btn" type="button" disabled={Boolean(busy)} onClick={saveBundle}>
          <Database size={15} aria-hidden="true" />
          Lưu bundle 8 video
        </button>
        <strong>Lưu và gửi video & frames</strong>
        <span>Ghi metadata vào database/video_list.json, tạo link tải và đồng bộ hiển thị cho bệnh nhân + Bác sĩ/KTV.</span>
      </div>
      <div className="artifact-export-grid">
        {phaseButtons.map((phase) => (
          <div key={phase.key} className="artifact-export-row">
            <b>{phase.label}</b>
            <button type="button" disabled={Boolean(busy)} onClick={() => prepare("video", phase.key)}>
              <Download size={15} aria-hidden="true" />
              Lưu & gửi video
            </button>
            <button type="button" disabled={Boolean(busy)} onClick={() => prepare("frames", phase.key)}>
              <Download size={15} aria-hidden="true" />
              Lưu & gửi frames
            </button>
            {(["video", "frames"] as const).map((kind) => {
              const item = links[`${kind}-${phase.key}`];
              return item?.url ? (
                <a key={kind} href={mediaUrl(item.url)} download={item.filename}>
                  Tải {kind === "video" ? "video" : "frames"} {formatBytes(item.size)}
                </a>
              ) : null;
            })}
          </div>
        ))}
      </div>
      {busy ? <small>Đang chuẩn bị {busy.includes("frames") ? "frames" : "video"}...</small> : null}
      {message ? <div className={`alert ${message.includes("Không") || message.includes("Chưa") ? "error" : "success"}`}>{message}</div> : null}
    </div>
  );
}

function fmtNumber(value: unknown, digits = 1) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "N/A";
  return num.toFixed(digits);
}

function fmtMetric(value: unknown, digits = 2, fallback = "N/A") {
  const num = Number(value);
  if (!Number.isFinite(num)) return fallback;
  return num.toFixed(digits);
}

function fmtInt(value: unknown, fallback = "0") {
  const num = Number(value);
  if (!Number.isFinite(num)) return fallback;
  return String(Math.round(num));
}

function hasLatestAiBundle(video: Record<string, unknown>) {
  return asText(video.latest_bundle_updated_at) !== "N/A";
}

function hasAiResult(video: Record<string, unknown>) {
  const metrics = video.metrics && typeof video.metrics === "object" ? (video.metrics as Record<string, unknown>) : {};
  const statusText = asText(video.status)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  const hasAccuracy = Number.isFinite(Number(video.accuracy ?? metrics.do_chinh_xac ?? metrics.ty_le_tong_the));
  const hasFrameMetrics = ["frame_dung", "frame_gan_dung", "frame_sai", "frame_khong_nhan_dang", "tong_frame_da_cham"].some(
    (key) => Number(metrics[key] ?? video[key] ?? 0) > 0,
  );
  return hasLatestAiBundle(video) || hasAccuracy || hasFrameMetrics || statusText.includes("da phan tich") || statusText.includes("done") || statusText.includes("success");
}

function researcherAiVideoCount(payload: DashboardPayload) {
  const bundleVideos = payload.videos.filter(hasLatestAiBundle);
  if (bundleVideos.length) return bundleVideos.length;
  const latestEvaluatedVideos = (payload.latest_evaluated_videos || []).filter(hasAiResult);
  if (latestEvaluatedVideos.length) return latestEvaluatedVideos.length;
  const scopedAiVideos = payload.videos.filter(hasAiResult);
  return scopedAiVideos.length || payload.metrics.videos_done;
}

function safeDownloadName(value: string) {
  return (
    value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/gi, "-")
      .replace(/^-+|-+$/g, "")
      .toLowerCase() || "rehab-chart"
  );
}

function inlineComputedStyles(source: Element, target: Element) {
  const computed = window.getComputedStyle(source);
  let cssText = "";
  for (let index = 0; index < computed.length; index += 1) {
    const property = computed.item(index);
    cssText += `${property}:${computed.getPropertyValue(property)};`;
  }
  target.setAttribute("style", cssText);
  const sourceChildren = Array.from(source.children);
  const targetChildren = Array.from(target.children);
  sourceChildren.forEach((child, index) => {
    const targetChild = targetChildren[index];
    if (targetChild) inlineComputedStyles(child, targetChild);
  });
}

async function svgStringToPngBlob(svg: string, width: number, height: number) {
  const imageUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  try {
    const image = new Image();
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () => reject(new Error("chart-image-load-failed"));
      image.src = imageUrl;
    });
    const scale = Math.min(2, window.devicePixelRatio || 1);
    const canvas = document.createElement("canvas");
    canvas.width = Math.ceil(width * scale);
    canvas.height = Math.ceil(height * scale);
    const context = canvas.getContext("2d");
    if (!context) throw new Error("canvas-not-supported");
    context.scale(scale, scale);
    context.drawImage(image, 0, 0, width, height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/png", 0.95));
    if (!blob) throw new Error("chart-export-failed");
    return blob;
  } finally {
    // Data URLs do not need explicit cleanup.
  }
}

async function elementToPngBlobViaForeignObject(element: HTMLElement) {
  const rect = element.getBoundingClientRect();
  const width = Math.max(240, Math.ceil(rect.width));
  const height = Math.max(180, Math.ceil(rect.height));
  const clone = element.cloneNode(true) as HTMLElement;
  inlineComputedStyles(element, clone);
  clone.querySelectorAll("button, a").forEach((node) => node.remove());
  clone.setAttribute("xmlns", "http://www.w3.org/1999/xhtml");
  const serialized = new XMLSerializer().serializeToString(clone);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><foreignObject width="100%" height="100%">${serialized}</foreignObject></svg>`;
  return svgStringToPngBlob(svg, width, height);
}

async function svgElementToPngBlob(svgElement: SVGSVGElement) {
  const rect = svgElement.getBoundingClientRect();
  const width = Math.max(240, Math.ceil(rect.width || svgElement.viewBox.baseVal.width || 520));
  const height = Math.max(180, Math.ceil(rect.height || svgElement.viewBox.baseVal.height || 240));
  const clone = svgElement.cloneNode(true) as SVGSVGElement;
  inlineComputedStyles(svgElement, clone);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height));
  if (!clone.getAttribute("viewBox")) {
    clone.setAttribute("viewBox", `0 0 ${width} ${height}`);
  }
  const serialized = new XMLSerializer().serializeToString(clone);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="100%" height="100%" fill="#ffffff"/>${serialized}</svg>`;
  return svgStringToPngBlob(svg, width, height);
}

async function elementToPngBlob(element: HTMLElement) {
  try {
    return await elementToPngBlobViaForeignObject(element);
  } catch {
    const svgElement = element.querySelector("svg");
    if (svgElement instanceof SVGSVGElement) {
      return svgElementToPngBlob(svgElement);
    }
    throw new Error("chart-export-failed");
  }
}

function downloadBlob(blob: Blob, filename: string) {
  const pngUrl = URL.createObjectURL(blob);
  browserDownload(pngUrl, filename.endsWith(".png") ? filename : `${filename}.png`);
  window.setTimeout(() => URL.revokeObjectURL(pngUrl), 1200);
}

async function blobToDataUrl(blob: Blob) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("blob-read-failed"));
    reader.readAsDataURL(blob);
  });
}

function DownloadableChartCard({
  title,
  filename,
  wide = false,
  onSaveImage,
  children,
}: {
  title: string;
  filename: string;
  wide?: boolean;
  onSaveImage?: (payload: { title: string; filename: string; blob: Blob; imageData: string }) => Promise<void> | void;
  children: ReactNode;
}) {
  const cardRef = useRef<HTMLElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [zooming, setZooming] = useState(false);
  const [failed, setFailed] = useState(false);
  const [zoomOpen, setZoomOpen] = useState(false);
  const saveImage = async () => {
    if (!cardRef.current) return;
    setBusy(true);
    setFailed(false);
    try {
      const finalFilename = filename.endsWith(".png") ? filename : `${filename}.png`;
      const blob = await elementToPngBlob(cardRef.current);
      downloadBlob(blob, finalFilename);
      if (onSaveImage) {
        await onSaveImage({ title, filename: finalFilename, blob, imageData: await blobToDataUrl(blob) });
      }
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  };
  const openZoom = async () => {
    setZooming(true);
    setFailed(false);
    try {
      setZoomOpen(true);
    } catch {
      setFailed(true);
    } finally {
      setZooming(false);
    }
  };
  return (
    <>
      <article ref={cardRef} className={wide ? "wide-chart-card downloadable-chart-card" : "downloadable-chart-card"}>
        <div className="chart-card-head">
          <h3>{title}</h3>
          <div className="chart-card-actions">
            <button type="button" className="chart-download-btn" onClick={openZoom} disabled={zooming} title={`Xem lớn ${title}`}>
              {zooming ? <RefreshCw size={14} className="spin" aria-hidden="true" /> : <Eye size={14} aria-hidden="true" />}
              Xem lớn
            </button>
            <button type="button" className="chart-download-btn" onClick={saveImage} disabled={busy} title={`Tải ảnh ${title}`}>
              {busy ? <RefreshCw size={14} className="spin" aria-hidden="true" /> : <Download size={14} aria-hidden="true" />}
              Tải ảnh
            </button>
          </div>
        </div>
        {children}
        {failed ? <small className="chart-export-error">Không mở/tải được ảnh biểu đồ này.</small> : null}
      </article>
      {zoomOpen && typeof document !== "undefined" ? createPortal(
        <div className="frame-modal chart-zoom-modal" role="dialog" aria-modal="true" onClick={() => setZoomOpen(false)}>
          <div className="frame-modal-inner chart-zoom-modal-inner" onClick={(event) => event.stopPropagation()}>
            <div className="frame-modal-head">
              <strong>{title}</strong>
              <button type="button" onClick={() => setZoomOpen(false)}>Đóng</button>
            </div>
            <div className="chart-zoom-content">{children}</div>
          </div>
        </div>,
        document.body,
      ) : null}
    </>
  );
}

function MultiLineChart({
  series,
}: {
  series: { label: string; color: string; dashed?: boolean; points: { x: number; y: number }[] }[];
}) {
  const visible = series.filter((item) => item.points.length);
  if (!visible.length) return <div className="empty-state">Chưa có dữ liệu góc khớp trong CSV.</div>;
  const width = 760;
  const height = 300;
  const pad = 42;
  const all = visible.flatMap((item) => item.points);
  const rawMinY = Math.min(...all.map((point) => point.y), 0);
  const rawMaxY = Math.max(...all.map((point) => point.y), 180);
  const minY = Math.max(0, Math.floor(rawMinY / 10) * 10 - 10);
  const maxY = Math.min(190, Math.ceil(rawMaxY / 10) * 10 + 10);
  const spanY = Math.max(1, maxY - minY);
  const minX = Math.min(...all.map((point) => point.x), 0);
  const maxX = Math.max(...all.map((point) => point.x), 1);
  const spanX = Math.max(1, maxX - minX);
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    value: minY + spanY * ratio,
    y: height - pad - ratio * (height - pad * 2),
  }));
  function pathFor(points: { x: number; y: number }[]) {
    return points
      .map((point, idx) => {
        const x = pad + ((point.x - minX) / spanX) * (width - pad * 2);
        const y = height - pad - ((point.y - minY) / spanY) * (height - pad * 2);
        return `${idx === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }
  return (
    <div className="chart-shell">
      <svg className="result-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Biểu đồ góc khớp">
        {yTicks.map((tick) => (
          <g key={tick.value}>
            <line className="chart-grid-line" x1={pad} y1={tick.y} x2={width - pad} y2={tick.y} />
            <text x={8} y={tick.y + 4}>{Math.round(tick.value)}</text>
          </g>
        ))}
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} />
        <line x1={pad} y1={pad} x2={pad} y2={height - pad} />
        {visible.map((item) => (
          <path key={item.label} d={pathFor(item.points)} style={{ stroke: item.color }} strokeDasharray={item.dashed ? "8 7" : undefined} />
        ))}
        <text className="chart-axis-label" x={width - 82} y={height - 10}>Frame</text>
        <text className="chart-axis-label" x={pad + 4} y={22}>Góc (°)</text>
      </svg>
      <div className="chart-legend">
        {visible.map((item) => (
          <span key={item.label} className={item.dashed ? "dashed" : undefined}><i style={{ background: item.color }} />{item.label}</span>
        ))}
      </div>
    </div>
  );
}

function HistogramChart({ bins, color }: { bins: { x0: number; x1: number; count: number }[]; color: string }) {
  if (!bins.length) return <div className="empty-state">Chưa có histogram.</div>;
  const width = 520;
  const height = 240;
  const padLeft = 46;
  const padBottom = 36;
  const padTop = 18;
  const padRight = 16;
  const chartWidth = width - padLeft - padRight;
  const chartHeight = height - padTop - padBottom;
  const maxCount = Math.max(...bins.map((bin) => bin.count), 1);
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    value: Math.round(maxCount * ratio),
    y: padTop + chartHeight - chartHeight * ratio,
  }));
  const step = chartWidth / Math.max(1, bins.length);
  const xTickIndexes = Array.from(new Set([0, Math.floor((bins.length - 1) / 2), bins.length - 1])).filter((index) => index >= 0);
  return (
    <svg className="histogram-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Histogram góc khớp">
      {yTicks.map((tick) => (
        <g key={`${tick.value}-${tick.y}`}>
          <line className="chart-grid-line" x1={padLeft} y1={tick.y} x2={width - padRight} y2={tick.y} />
          <text className="chart-tick" x={8} y={tick.y + 4}>{tick.value}</text>
        </g>
      ))}
      <line x1={padLeft} y1={padTop} x2={padLeft} y2={height - padBottom} />
      <line x1={padLeft} y1={height - padBottom} x2={width - padRight} y2={height - padBottom} />
      {bins.map((bin, index) => {
        const barHeight = Math.max(2, (Number(bin.count || 0) / maxCount) * chartHeight);
        const x = padLeft + index * step + step * 0.12;
        const y = height - padBottom - barHeight;
        return (
          <rect
            key={`${bin.x0}-${bin.x1}`}
            x={x}
            y={y}
            width={Math.max(3, step * 0.76)}
            height={barHeight}
            rx={3}
            style={{ fill: color }}
          >
            <title>{`${fmtNumber(bin.x0)}-${fmtNumber(bin.x1)}°: ${bin.count}`}</title>
          </rect>
        );
      })}
      {xTickIndexes.map((sourceIndex) => {
        const bin = bins[sourceIndex];
        const x = padLeft + sourceIndex * step + step / 2;
        return <text key={`x-${sourceIndex}`} className="chart-tick" x={x - 10} y={height - 12}>{Math.round(bin.x0)}°</text>;
      })}
      <text className="chart-axis-label" x={width - 72} y={height - 12}>Góc</text>
      <text className="chart-axis-label" x={padLeft + 2} y={12}>Số frame</text>
    </svg>
  );
}

function ResultDistributionChart({ data, centerMode = "pass" }: { data: { label: string; value: number }[]; centerMode?: "pass" | "total" }) {
  const total = data.reduce((sum, item) => sum + Number(item.value || 0), 0);
  if (!total) return <div className="empty-state">Chưa có phân bố PASS/NEAR/FAIL/UNKNOWN.</div>;
  let current = 0;
  const colors: Record<string, string> = {
    PASS: "#10b981",
    NEAR: "#f59e0b",
    FAIL: "#ef4444",
    UNKNOWN: "#64748b",
    "Đúng": "#10b981",
    "Gần đúng": "#f59e0b",
    "Sai": "#ef4444",
    "Chưa rõ": "#64748b",
  };
  const passValue = data.find((item) => ["PASS", "Đúng"].includes(item.label))?.value || 0;
  const gradient = data
    .map((item) => {
      const start = (current / total) * 100;
      current += Number(item.value || 0);
      const end = (current / total) * 100;
      return `${colors[item.label] || "#0284c7"} ${start}% ${end}%`;
    })
    .join(", ");
  return (
    <div className="result-distribution">
      <div className="donut-chart" style={{ background: `conic-gradient(${gradient})` }}>
        <span>
          <b>{centerMode === "total" ? fmtInt(total) : `${fmtNumber((Number(passValue) / total) * 100, 0)}%`}</b>
          {centerMode === "total" ? "phiếu" : "Đúng"}
        </span>
      </div>
      <div className="distribution-bars">
        {data.map((item) => (
          <div key={item.label}>
            <span><i style={{ background: colors[item.label] || "#0284c7" }} />{item.label === "UNKNOWN" ? "UNKNOWN - Không nhận dạng" : item.label}</span>
            <strong>{item.value}</strong>
            <em>
              <b style={{ width: `${Math.max(2, (Number(item.value || 0) / total) * 100)}%`, background: colors[item.label] || "#0284c7" }} />
            </em>
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniBarChart({ data, unit = "" }: { data: { label: string; value: number }[]; unit?: string }) {
  if (!data.length) return <div className="empty-state">Chưa có dữ liệu biểu đồ.</div>;
  const max = Math.max(...data.map((item) => Number(item.value || 0)), 1);
  return (
    <div className="mini-bar-chart">
      {data.slice(0, 6).map((item, index) => (
        <div className="mini-bar-row" key={`${item.label}-${index}`}>
          <span>{compactText(item.label, 34)}</span>
          <div className="mini-bar-track" aria-hidden="true">
            <em style={{ width: `${Math.max(5, (Number(item.value || 0) / max) * 100)}%` }} />
          </div>
          <b>{fmtInt(item.value)}{unit}</b>
        </div>
      ))}
    </div>
  );
}

function DynamicMetricStrip({ items, tone = "dark" }: { items: { label: string; value: number | string; hint: string; icon: typeof Activity }[]; tone?: "dark" | "light" }) {
  return (
    <div className={`dynamic-metric-strip ${tone}`}>
      {items.map(({ icon: Icon, label, value, hint }, index) => (
        <article key={label} style={{ animationDelay: `${index * 70}ms` }}>
          <Icon size={18} aria-hidden="true" />
          <div>
            <b>{value}</b>
            <span>{label}</span>
            <small>{hint}</small>
          </div>
        </article>
      ))}
    </div>
  );
}

function BoxPlotChart({ items, color }: { items: BoxPlotItem[]; color: string }) {
  if (!items.length) return <div className="empty-state">Chưa có dữ liệu boxplot.</div>;
  const min = Math.min(...items.map((item) => item.min));
  const max = Math.max(...items.map((item) => item.max));
  const span = Math.max(1, max - min);
  const pos = (value: number) => `${((value - min) / span) * 100}%`;
  return (
    <div className="boxplot-list">
      {items.map((item) => (
        <div className="boxplot-row" key={item.label}>
          <b>{item.label}</b>
          <div className="boxplot-track">
            <span className="boxplot-whisker" style={{ left: pos(item.min), width: `calc(${pos(item.max)} - ${pos(item.min)})` }} />
            <span className="boxplot-box" style={{ left: pos(item.q1), width: `calc(${pos(item.q3)} - ${pos(item.q1)})`, borderColor: color }} />
            <span className="boxplot-mid" style={{ left: pos(item.median), background: color }} />
          </div>
          <small>{fmtNumber(item.median)}° · n={item.count || 0}</small>
        </div>
      ))}
    </div>
  );
}

function StatusBoxPlotChart({ items, color }: { items: BoxPlotItem[]; color: string }) {
  const requiredLabels = ["PASS", "NEAR", "FAIL"];
  const normalized = [
    ...requiredLabels.map((label) => items.find((item) => item.label.toUpperCase() === label) || ({ label, count: 0 } as BoxPlotItem)),
    ...items.filter((item) => !requiredLabels.includes(item.label.toUpperCase())),
  ];
  const validItems = normalized.filter((item) => Number.isFinite(item.min) && Number.isFinite(item.max));
  if (!validItems.length) return <div className="empty-state">Chưa có dữ liệu boxplot.</div>;
  const width = 520;
  const height = 260;
  const padLeft = 46;
  const padRight = 18;
  const padTop = 18;
  const padBottom = 42;
  const chartWidth = width - padLeft - padRight;
  const chartHeight = height - padTop - padBottom;
  const yTicks = [0, 48, 95, 143, 190];
  const min = 0;
  const max = 190;
  const span = max - min;
  const yFor = (value: number) => padTop + ((max - Math.max(min, Math.min(max, value))) / span) * chartHeight;
  const band = chartWidth / normalized.length;
  const hasBoxData = (item: BoxPlotItem) => Number.isFinite(item.min) && Number.isFinite(item.max) && Number(item.count || 0) > 0;
  return (
    <svg className="status-boxplot-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Boxplot theo kết quả">
      {yTicks.map((tick) => {
        const y = yFor(tick);
        return (
          <g key={tick}>
            <line className="chart-grid-line" x1={padLeft} y1={y} x2={width - padRight} y2={y} />
            <text className="chart-tick" x={8} y={y + 4}>{tick}</text>
          </g>
        );
      })}
      <line x1={padLeft} y1={padTop} x2={padLeft} y2={height - padBottom} />
      <line x1={padLeft} y1={height - padBottom} x2={width - padRight} y2={height - padBottom} />
      <text className="chart-axis-label" x={padLeft + 2} y={12}>Góc (°)</text>
      <text className="chart-axis-label" x={width - 70} y={height - 12}>Kết quả</text>
      {normalized.map((item, index) => {
        const centerX = padLeft + band * index + band / 2;
        const boxWidth = Math.min(52, band * 0.42);
        const emptyWidth = Math.min(58, band * 0.5);
        const hasData = hasBoxData(item);
        if (!hasData) {
          return (
            <g key={item.label}>
              <rect
                className="boxplot-empty-box"
                x={centerX - emptyWidth / 2}
                y={padTop + 18}
                width={emptyWidth}
                height={chartHeight - 36}
                rx={10}
              />
              <text className="chart-category" x={centerX} y={height - padBottom + 20}>{item.label}</text>
              <text className="boxplot-empty-label" x={centerX} y={height - 8}>chưa có dữ liệu</text>
            </g>
          );
        }
        const minY = yFor(item.min);
        const maxY = yFor(item.max);
        const q1Y = yFor(item.q1);
        const q3Y = yFor(item.q3);
        const medianY = yFor(item.median);
        const boxY = Math.min(q1Y, q3Y);
        const boxHeight = Math.max(3, Math.abs(q1Y - q3Y));
        return (
          <g key={item.label}>
            <line className="boxplot-whisker-line" x1={centerX} y1={maxY} x2={centerX} y2={minY} />
            <line className="boxplot-cap-line" x1={centerX - boxWidth * 0.36} y1={maxY} x2={centerX + boxWidth * 0.36} y2={maxY} style={{ stroke: color }} />
            <line className="boxplot-cap-line" x1={centerX - boxWidth * 0.36} y1={minY} x2={centerX + boxWidth * 0.36} y2={minY} style={{ stroke: color }} />
            <rect
              className="boxplot-svg-box"
              x={centerX - boxWidth / 2}
              y={boxY}
              width={boxWidth}
              height={boxHeight}
              rx={4}
              style={{ stroke: color }}
            />
            <line
              className="boxplot-median-line"
              x1={centerX - boxWidth * 0.58}
              y1={medianY}
              x2={centerX + boxWidth * 0.58}
              y2={medianY}
              style={{ stroke: color }}
            />
            <text className="chart-category" x={centerX} y={height - padBottom + 20}>{item.label}</text>
            <text className="boxplot-value-label" x={centerX} y={height - 8}>{fmtNumber(item.median)}° · n={item.count || 0}</text>
            <title>{`${item.label}: min ${fmtNumber(item.min)}°, Q1 ${fmtNumber(item.q1)}°, median ${fmtNumber(item.median)}°, Q3 ${fmtNumber(item.q3)}°, max ${fmtNumber(item.max)}°, n=${item.count || 0}`}</title>
          </g>
        );
      })}
    </svg>
  );
}

function RadarChart({ radar }: { radar?: { labels: string[]; values: number[]; targets: number[] } }) {
  if (!radar?.labels?.length) return <div className="empty-state">Chưa có chỉ số radar.</div>;
  const size = 260;
  const center = size / 2;
  const radius = 96;
  const labels = radar.labels;
  function point(value: number, idx: number) {
    const angle = -Math.PI / 2 + (idx / labels.length) * Math.PI * 2;
    const r = radius * Math.max(0, Math.min(1, value));
    return `${center + Math.cos(angle) * r},${center + Math.sin(angle) * r}`;
  }
  const actual = labels.map((_, idx) => point(radar.values[idx] || 0, idx)).join(" ");
  const target = labels.map((_, idx) => point(radar.targets[idx] || 0, idx)).join(" ");
  return (
    <svg className="radar-chart" viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Radar chỉ số nghiên cứu">
      {[0.25, 0.5, 0.75, 1].map((level) => (
        <g key={level}>
          <polygon points={labels.map((_, idx) => point(level, idx)).join(" ")} />
          <text className="radar-scale" x={center + 4} y={center - radius * level + 4}>{Math.round(level * 100)}</text>
        </g>
      ))}
      {labels.map((label, idx) => {
        const [x, y] = point(1.14, idx).split(",");
        return <text key={label} x={x} y={y}>{label}</text>;
      })}
      <polygon className="radar-target" points={target} />
      <polygon className="radar-actual" points={actual} />
    </svg>
  );
}

function RadarLegend() {
  return (
    <div className="radar-legend" aria-label="Chú thích radar">
      <span><i className="radar-legend-actual" />Viền xanh dương: chỉ số thực tế</span>
      <span><i className="radar-legend-target" />Viền xanh lá: mục tiêu/chuẩn tham chiếu</span>
    </div>
  );
}

function RadarMetricNumbers({ metrics, phaseLabel }: { metrics?: Record<string, number | string>; phaseLabel?: string }) {
  const rows = [
    { label: "Accuracy", value: metrics?.accuracy, unit: "%", digits: 2 },
    { label: "Tổng frame", value: metrics?.total_frames, unit: "", digits: 0 },
    { label: "PASS", value: metrics?.pass_frames, unit: "", digits: 0 },
    { label: "NEAR", value: metrics?.near_frames, unit: "", digits: 0 },
    { label: "FAIL", value: metrics?.fail_frames, unit: "", digits: 0 },
    { label: "UNKNOWN", value: metrics?.unknown_frames, unit: "", digits: 0 },
    { label: "F1-score", value: metrics?.f1_score, unit: "", digits: 3 },
    { label: "MAE", value: metrics?.mae, unit: "°", digits: 2 },
    { label: "ICC", value: metrics?.icc, unit: "", digits: 3 },
    { label: "Precision", value: metrics?.precision, unit: "", digits: 3 },
    { label: "Recall", value: metrics?.recall, unit: "", digits: 3 },
  ];
  return (
    <div className="radar-metric-panel" aria-label={`Radar metrics ${phaseLabel || ""}`}>
      {phaseLabel ? <small>{phaseLabel}</small> : null}
      <div className="radar-metric-grid">
        {rows.map((row) => (
          <span key={row.label}>
            <b>{row.label}</b>
            <strong>{typeof row.value === "number" ? fmtNumber(row.value, row.digits) : asText(row.value)}{row.unit}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}

function histogramFromPoints(points: { x: number; y: number }[], bins = 16) {
  const values = points.map((point) => Number(point.y)).filter((value) => Number.isFinite(value));
  if (!values.length) return [];
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  if (lo === hi) return [{ x0: lo, x1: hi, count: values.length }];
  const width = (hi - lo) / bins;
  const counts = Array.from({ length: bins }, () => 0);
  values.forEach((value) => {
    const index = Math.min(bins - 1, Math.floor((value - lo) / width));
    counts[index] += 1;
  });
  return counts.map((count, index) => ({ x0: lo + index * width, x1: lo + (index + 1) * width, count }));
}

function boxplotFromPoints(points: { x: number; y: number }[], label: string): BoxPlotItem[] {
  const values = points.map((point) => Number(point.y)).filter((value) => Number.isFinite(value)).sort((a, b) => a - b);
  if (!values.length) return [];
  const pick = (percent: number) => {
    if (values.length === 1) return values[0];
    const pos = (values.length - 1) * percent;
    const low = Math.floor(pos);
    const high = Math.min(values.length - 1, low + 1);
    const frac = pos - low;
    return values[low] * (1 - frac) + values[high] * frac;
  };
  return [{
    label,
    min: values[0],
    q1: pick(0.25),
    median: pick(0.5),
    q3: pick(0.75),
    max: values[values.length - 1],
    mean: values.reduce((sum, value) => sum + value, 0) / values.length,
    count: values.length,
  }];
}

function ResearchMetricsTable({ metrics }: { metrics?: Record<string, number | string> }) {
  const rows = [
    ["Accuracy", metrics?.accuracy, "%"],
    ["Tổng frame", metrics?.total_frames, ""],
    ["PASS / NEAR / FAIL / UNKNOWN", `${metrics?.pass_frames || 0} / ${metrics?.near_frames || 0} / ${metrics?.fail_frames || 0} / ${metrics?.unknown_frames || 0}`, ""],
    ["Góc vai TB", metrics?.shoulder_mean, "°"],
    ["Góc khuỷu TB", metrics?.elbow_mean, "°"],
    ["MAE", metrics?.mae, "°"],
    ["F1-score", metrics?.f1_score, ""],
    ["ICC", metrics?.icc, ""],
    ["Precision", metrics?.precision, ""],
    ["Recall", metrics?.recall, ""],
  ];
  return (
    <div className="metrics-table">
      {rows.map(([label, value, unit]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{typeof value === "number" ? fmtNumber(value, label === "Tổng frame" ? 0 : 2) : asText(value)}{unit}</strong>
        </div>
      ))}
    </div>
  );
}

function JointAngleChart({
  series,
}: {
  series: { label: string; color: string; dashed?: boolean; points: { x: number; y: number }[] }[];
}) {
  const visible = series.filter((item) => item.points.length);
  if (!visible.length) return <div className="empty-state">Chưa có dữ liệu góc khớp trong CSV.</div>;
  const width = 760;
  const height = 300;
  const pad = 42;
  const all = visible.flatMap((item) => item.points);
  const rawMinY = Math.min(...all.map((point) => point.y), 0);
  const rawMaxY = Math.max(...all.map((point) => point.y), 180);
  const minY = Math.max(0, Math.floor(rawMinY / 10) * 10 - 10);
  const maxY = Math.min(190, Math.ceil(rawMaxY / 10) * 10 + 10);
  const spanY = Math.max(1, maxY - minY);
  const minX = Math.min(...all.map((point) => point.x), 0);
  const maxX = Math.max(...all.map((point) => point.x), 1);
  const spanX = Math.max(1, maxX - minX);
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    value: minY + spanY * ratio,
    y: height - pad - ratio * (height - pad * 2),
  }));
  const pathFor = (points: { x: number; y: number }[]) =>
    points
      .map((point, idx) => {
        const x = pad + ((point.x - minX) / spanX) * (width - pad * 2);
        const y = height - pad - ((point.y - minY) / spanY) * (height - pad * 2);
        return `${idx === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  return (
    <div className="chart-shell">
      <svg className="result-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Biểu đồ góc khớp">
        {yTicks.map((tick) => (
          <g key={tick.value}>
            <line className="chart-grid-line" x1={pad} y1={tick.y} x2={width - pad} y2={tick.y} />
            <text x={8} y={tick.y + 4}>{Math.round(tick.value)}</text>
          </g>
        ))}
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} />
        <line x1={pad} y1={pad} x2={pad} y2={height - pad} />
        {visible.map((item) => (
          <path key={item.label} d={pathFor(item.points)} style={{ stroke: item.color }} strokeDasharray={item.dashed ? "8 7" : undefined} />
        ))}
        <text className="chart-axis-label" x={width - 82} y={height - 10}>Frame</text>
        <text className="chart-axis-label" x={pad + 4} y={22}>Góc (°)</text>
      </svg>
      <div className="chart-legend">
        {visible.map((item) => (
          <span key={item.label} className={item.dashed ? "dashed" : undefined}><i style={{ background: item.color }} />{item.label}</span>
        ))}
      </div>
    </div>
  );
}

function radarFromMetrics(metrics?: Record<string, number | string>) {
  const value = (key: string) => Number(metrics?.[key] ?? 0);
  const maeInverse = Math.max(0, Math.min(1, 1 - value("mae") / 60));
  return {
    labels: ["Accuracy", "F1-score", "MAE inverse", "ICC", "Precision", "Recall"],
    values: [
      Math.max(0, Math.min(1, value("accuracy") / 100)),
      Math.max(0, Math.min(1, value("f1_score"))),
      maeInverse,
      Math.max(0, Math.min(1, value("icc"))),
      Math.max(0, Math.min(1, value("precision"))),
      Math.max(0, Math.min(1, value("recall"))),
    ],
    targets: [0.9, 0.85, 0.65, 0.75, 0.85, 0.85],
  };
}

function AnalysisCharts({
  chart,
  onSendCharts,
  onSaveChartImage,
}: {
  chart: VideoDetailPayload["chart"];
  onSendCharts?: (phaseLabel: string, metrics: Record<string, unknown>) => Promise<void> | void;
  onSaveChartImage?: (payload: {
    phase: string;
    phaseLabel: string;
    chartName: string;
    filename: string;
    imageData: string;
    metrics: Record<string, unknown>;
  }) => Promise<void> | void;
}) {
  const shoulder = chart.series?.shoulder || chart.points || [];
  const elbow = chart.series?.elbow || [];
  const shoulderRef = chart.series?.shoulder_ref || [];
  const elbowRef = chart.series?.elbow_ref || [];
  const codmanPhaseRanges = (chart.phase_ranges || []).filter((phase) => ["g1", "g2", "g3"].includes(phase.key));
  const phaseOptions = [{ key: "all", label: "Tất cả", threshold: null, start: 0, end: Number.POSITIVE_INFINITY }, ...codmanPhaseRanges];
  const [chartPhase, setChartPhase] = useState("all");
  const selectedPhase = phaseOptions.find((item) => item.key === chartPhase) || phaseOptions[0];
  const withinPhase = (point: { x: number; y: number }) => selectedPhase.key === "all" || (point.x >= selectedPhase.start && point.x <= selectedPhase.end);
  const shoulderVisible = shoulder.filter(withinPhase);
  const elbowVisible = elbow.filter(withinPhase);
  const shoulderRefVisible = shoulderRef.filter(withinPhase);
  const elbowRefVisible = elbowRef.filter(withinPhase);
  const selectedPhaseBoxplot = chart.phase_boxplots?.find((item) => item.key === selectedPhase.key);
  const selectedPhasePie = selectedPhase.key === "all" ? null : chart.phase_pies?.find((item) => item.key === selectedPhase.key);
  const selectedPhaseMetrics = selectedPhase.key === "all" ? null : chart.phase_metrics?.find((item) => item.key === selectedPhase.key);
  const selectedMetrics = selectedPhaseMetrics?.metrics || chart.research_metrics || {};
  const chartFileBase = safeDownloadName(`bieu-do-${selectedPhase.label}`);
  const [sendMessage, setSendMessage] = useState("");
  const [sendingCharts, setSendingCharts] = useState(false);
  const distributionData = selectedPhasePie?.pie || chart.pie || [];
  const shoulderBoxplotItems = selectedPhase.key === "all" ? chart.boxplots?.shoulder || [] : selectedPhaseBoxplot?.shoulder || boxplotFromPoints(shoulderVisible, selectedPhase.label);
  const elbowBoxplotItems = selectedPhase.key === "all" ? chart.boxplots?.elbow || [] : selectedPhaseBoxplot?.elbow || boxplotFromPoints(elbowVisible, selectedPhase.label);
  const summaryDigits = (label: string) => (label.includes("frame") || ["PASS", "NEAR", "FAIL", "UNKNOWN"].includes(label) ? 0 : 2);
  const summaryItems = [
    { label: "Accuracy", value: selectedMetrics.accuracy ?? "--", unit: "%" },
    { label: "Tổng frame", value: selectedMetrics.total_frames ?? chart.row_count ?? "--", unit: "" },
    { label: "PASS", value: selectedMetrics.pass_frames ?? 0, unit: "" },
    { label: "NEAR", value: selectedMetrics.near_frames ?? 0, unit: "" },
    { label: "FAIL", value: selectedMetrics.fail_frames ?? 0, unit: "" },
    { label: "UNKNOWN", value: selectedMetrics.unknown_frames ?? 0, unit: "" },
    { label: "MAE", value: selectedMetrics.mae ?? "--", unit: "°" },
  ];
  const sendCurrentCharts = async () => {
    if (!onSendCharts) return;
    setSendingCharts(true);
    setSendMessage("");
    try {
      await onSendCharts(selectedPhase.label, selectedMetrics);
      setSendMessage(`Đã lưu và gửi biểu đồ ${selectedPhase.label} cho bệnh nhân + Bác sĩ/KTV.`);
    } catch (error) {
      setSendMessage(error instanceof ApiError ? error.message : "Không gửi được biểu đồ đang xem.");
    } finally {
      setSendingCharts(false);
    }
  };
  const saveChartImage = async ({ title, filename, imageData }: { title: string; filename: string; imageData: string }) => {
    if (!onSaveChartImage) return;
    await onSaveChartImage({
      phase: selectedPhase.key,
      phaseLabel: selectedPhase.label,
      chartName: title,
      filename,
      imageData,
      metrics: selectedMetrics,
    });
  };
  return (
    <section className="result-card chart-dashboard">
      <div className="panel-title chart-title-row">
        <div>
          <BarChart3 size={18} aria-hidden="true" />
          <h2>Biểu đồ phân tích</h2>
        </div>
        {onSendCharts ? (
          <button className="chart-send-btn" type="button" onClick={sendCurrentCharts} disabled={sendingCharts}>
            {sendingCharts ? <RefreshCw size={15} className="spin" aria-hidden="true" /> : <Mail size={15} aria-hidden="true" />}
            Lưu & gửi biểu đồ đang xem
          </button>
        ) : null}
      </div>
      {sendMessage ? <div className={`alert ${sendMessage.includes("Không") ? "error" : "success"}`}>{sendMessage}</div> : null}
      {phaseOptions.length > 2 ? (
        <div className="chart-phase-row" role="tablist" aria-label="Giai đoạn biểu đồ">
          {phaseOptions.map((phase) => (
            <button key={phase.key} type="button" className={chartPhase === phase.key ? "active" : ""} onClick={() => setChartPhase(phase.key)}>
              <b>{phase.label}</b>
              {phase.threshold ? <span>REF ±{phase.threshold}°</span> : null}
            </button>
          ))}
        </div>
      ) : null}
      <div className="chart-summary-strip">
        {summaryItems.map((item) => (
          <span key={item.label}>
            <b>{item.label}</b>
            <strong>{typeof item.value === "number" ? fmtNumber(item.value, summaryDigits(item.label)) : asText(item.value)}{item.unit}</strong>
          </span>
        ))}
      </div>
      <div className="chart-tabs-grid">
        <DownloadableChartCard wide title="Góc khớp theo frame" filename={`${chartFileBase}-goc-khop`} onSaveImage={onSaveChartImage ? saveChartImage : undefined}>
          <JointAngleChart
            series={[
              { label: "Góc vai", color: "#0284c7", points: shoulderVisible },
              { label: "Góc khuỷu", color: "#dc2626", points: elbowVisible },
              { label: "Vai chuẩn", color: "#059669", dashed: true, points: shoulderRefVisible },
              { label: "Khuỷu chuẩn", color: "#7c3aed", dashed: true, points: elbowRefVisible },
            ]}
          />
        </DownloadableChartCard>
        <DownloadableChartCard title="Phân bố kết quả" filename={`${chartFileBase}-phan-bo`} onSaveImage={onSaveChartImage ? saveChartImage : undefined}>
          <ResultDistributionChart data={distributionData} />
          {selectedPhase.key !== "all" && selectedPhasePie ? (
            <small className="chart-phase-note">
              {selectedPhasePie.label}: PASS {selectedPhasePie.pass} · NEAR {selectedPhasePie.near} · FAIL {selectedPhasePie.fail} · UNKNOWN {selectedPhasePie.unknown || 0} · {fmtNumber(selectedPhasePie.accuracy, 1)}%
            </small>
          ) : null}
        </DownloadableChartCard>
        <DownloadableChartCard title="Histogram góc vai" filename={`${chartFileBase}-histogram-vai`} onSaveImage={onSaveChartImage ? saveChartImage : undefined}>
          <HistogramChart bins={selectedPhase.key === "all" ? chart.histograms?.shoulder || [] : histogramFromPoints(shoulderVisible)} color="#0284c7" />
        </DownloadableChartCard>
        <DownloadableChartCard title="Histogram góc khuỷu" filename={`${chartFileBase}-histogram-khuyu`} onSaveImage={onSaveChartImage ? saveChartImage : undefined}>
          <HistogramChart bins={selectedPhase.key === "all" ? chart.histograms?.elbow || [] : histogramFromPoints(elbowVisible)} color="#dc2626" />
        </DownloadableChartCard>
        <DownloadableChartCard title="Boxplot góc vai" filename={`${chartFileBase}-boxplot-vai`} onSaveImage={onSaveChartImage ? saveChartImage : undefined}>
          <StatusBoxPlotChart items={shoulderBoxplotItems} color="#0284c7" />
        </DownloadableChartCard>
        <DownloadableChartCard title="Boxplot góc khuỷu" filename={`${chartFileBase}-boxplot-khuyu`} onSaveImage={onSaveChartImage ? saveChartImage : undefined}>
          <StatusBoxPlotChart items={elbowBoxplotItems} color="#dc2626" />
        </DownloadableChartCard>
        <DownloadableChartCard title="Radar chỉ số nghiên cứu" filename={`${chartFileBase}-radar`} onSaveImage={onSaveChartImage ? saveChartImage : undefined}>
          <RadarChart radar={radarFromMetrics(selectedMetrics)} />
          <RadarLegend />
          <RadarMetricNumbers metrics={selectedMetrics} phaseLabel={selectedPhase.label} />
        </DownloadableChartCard>
        <DownloadableChartCard title="Bảng chỉ số nghiên cứu" filename={`${chartFileBase}-bang-chi-so`} onSaveImage={onSaveChartImage ? saveChartImage : undefined}>
          <ResearchMetricsTable metrics={selectedMetrics} />
        </DownloadableChartCard>
      </div>
    </section>
  );
}

function AnalysisChartsLegacy({ chart }: { chart: VideoDetailPayload["chart"] }) {
  const shoulder = chart.series?.shoulder || chart.points || [];
  const elbow = chart.series?.elbow || [];
  const shoulderRef = chart.series?.shoulder_ref || [];
  const elbowRef = chart.series?.elbow_ref || [];
  const codmanPhaseRanges = (chart.phase_ranges || []).filter((phase) => ["g1", "g2", "g3"].includes(phase.key));
  const phaseOptions = [{ key: "all", label: "Tất cả", threshold: null, start: 0, end: Number.POSITIVE_INFINITY }, ...codmanPhaseRanges];
  const [chartPhase, setChartPhase] = useState("all");
  const selectedPhase = phaseOptions.find((item) => item.key === chartPhase) || phaseOptions[0];
  const withinPhase = (point: { x: number; y: number }) => selectedPhase.key === "all" || (point.x >= selectedPhase.start && point.x <= selectedPhase.end);
  const shoulderVisible = shoulder.filter(withinPhase);
  const elbowVisible = elbow.filter(withinPhase);
  const shoulderRefVisible = shoulderRef.filter(withinPhase);
  const elbowRefVisible = elbowRef.filter(withinPhase);
  const selectedPhaseBoxplot = chart.phase_boxplots?.find((item) => item.key === selectedPhase.key);
  const shoulderBoxplotItems = selectedPhase.key === "all" ? chart.boxplots?.shoulder || [] : selectedPhaseBoxplot?.shoulder || boxplotFromPoints(shoulderVisible, selectedPhase.label);
  const elbowBoxplotItems = selectedPhase.key === "all" ? chart.boxplots?.elbow || [] : selectedPhaseBoxplot?.elbow || boxplotFromPoints(elbowVisible, selectedPhase.label);
  const metrics = chart.research_metrics || {};
  const summaryDigits = (label: string) => (label.includes("frame") || ["PASS", "NEAR", "FAIL", "UNKNOWN"].includes(label) ? 0 : 2);
  const summaryItems = [
    { label: "Accuracy", value: metrics.accuracy ?? "--", unit: "%" },
    { label: "Tổng frame", value: metrics.total_frames ?? chart.row_count ?? "--", unit: "" },
    { label: "PASS", value: metrics.pass_frames ?? 0, unit: "" },
    { label: "NEAR", value: metrics.near_frames ?? 0, unit: "" },
    { label: "FAIL", value: metrics.fail_frames ?? 0, unit: "" },
    { label: "UNKNOWN", value: metrics.unknown_frames ?? 0, unit: "" },
    { label: "MAE", value: metrics.mae ?? "--", unit: "°" },
  ];
  return (
    <section className="result-card chart-dashboard">
      <div className="panel-title">
        <BarChart3 size={18} aria-hidden="true" />
        <h2>Biểu đồ phân tích</h2>
      </div>
      {phaseOptions.length > 2 ? (
        <div className="chart-phase-row" role="tablist" aria-label="Giai đoạn biểu đồ">
          {phaseOptions.map((phase) => (
            <button key={phase.key} type="button" className={chartPhase === phase.key ? "active" : ""} onClick={() => setChartPhase(phase.key)}>
              <b>{phase.label}</b>
              {phase.threshold ? <span>REF ±{phase.threshold}°</span> : null}
            </button>
          ))}
        </div>
      ) : null}
      <div className="chart-summary-strip">
        {summaryItems.map((item) => (
          <span key={item.label}>
            <b>{item.label}</b>
            <strong>{typeof item.value === "number" ? fmtNumber(item.value, summaryDigits(item.label)) : asText(item.value)}{item.unit}</strong>
          </span>
        ))}
      </div>
      <div className="chart-tabs-grid">
        <article>
          <h3>Góc khớp theo frame</h3>
          <MultiLineChart
            series={[
              { label: "Góc vai", color: "#0284c7", points: shoulderVisible },
              { label: "Góc khuỷu", color: "#dc2626", points: elbowVisible },
              { label: "Vai chuẩn", color: "#059669", dashed: true, points: shoulderRefVisible },
              { label: "Khuỷu chuẩn", color: "#7c3aed", dashed: true, points: elbowRefVisible },
            ]}
          />
        </article>
        <article>
          <h3>Phân bố kết quả</h3>
          <ResultDistributionChart data={chart.pie || []} />
          {chart.phase_pies?.length ? (
            <div className="phase-distribution-grid">
              {chart.phase_pies.map((phase) => (
                <section key={phase.key}>
                  <h4>{phase.label}</h4>
                  <ResultDistributionChart data={phase.pie || []} />
                  <small>PASS {phase.pass} · NEAR {phase.near} · FAIL {phase.fail} · UNKNOWN {phase.unknown || 0} · {fmtNumber(phase.accuracy, 1)}%</small>
                </section>
              ))}
            </div>
          ) : null}
        </article>
        <article>
          <h3>Histogram góc vai</h3>
          <HistogramChart bins={selectedPhase.key === "all" ? chart.histograms?.shoulder || [] : histogramFromPoints(shoulderVisible)} color="#0284c7" />
        </article>
        <article>
          <h3>Histogram góc khuỷu</h3>
          <HistogramChart bins={selectedPhase.key === "all" ? chart.histograms?.elbow || [] : histogramFromPoints(elbowVisible)} color="#dc2626" />
        </article>
        <article>
          <h3>Boxplot góc vai</h3>
          <StatusBoxPlotChart items={shoulderBoxplotItems} color="#0284c7" />
        </article>
        <article>
          <h3>Boxplot góc khuỷu</h3>
          <StatusBoxPlotChart items={elbowBoxplotItems} color="#dc2626" />
        </article>
        <article>
          <h3>Radar chỉ số nghiên cứu</h3>
          <RadarChart radar={chart.radar} />
          <RadarLegend />
        </article>
        <article>
          <h3>Bảng chỉ số nghiên cứu</h3>
          <ResearchMetricsTable metrics={chart.research_metrics} />
        </article>
      </div>
    </section>
  );
}

function SidebarInfo({
  payload,
  nav,
  active,
  onSelect,
  onCollapse,
}: {
  payload: DashboardPayload;
  nav: ReturnType<typeof roleTabs>;
  active: ViewKey;
  onSelect: (tab: ViewKey) => void;
  onCollapse: () => void;
}) {
  const role = payload.user.role_key;
  const metrics = payload.metrics;
  const aiVideoDoneCount = researcherAiVideoCount(payload);
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark small">
          <HeartPulse size={22} aria-hidden="true" />
        </div>
        <div>
          <strong>{roleNames[role]}</strong>
          <span>{payload.user.full_name || payload.user.username}</span>
        </div>
        <button className="sidebar-collapse-btn" type="button" onClick={onCollapse} title="Thu sidebar">
          <PanelLeftClose size={18} aria-hidden="true" />
        </button>
      </div>
      <div className="user-tile">
        <strong>{payload.user.username}</strong>
        <span className={`role-pill ${roleClass(payload.user.role)}`}>{payload.user.role}</span>
      </div>
      <div className="side-nav-card">
        <div className="side-nav-head">
          <span>Menu chức năng</span>
          <b>{nav.length} tab</b>
        </div>
        <nav className="side-nav" aria-label="Menu chức năng">
          {nav.map((item, index) => {
            const Icon = item.icon;
            return (
              <button key={item.key} className={active === item.key ? "active" : ""} onClick={() => onSelect(item.key)} type="button">
                <Icon size={16} aria-hidden="true" />
                <span>{item.label}</span>
                <b>{index + 1}</b>
              </button>
            );
          })}
        </nav>
      </div>
      {role === "patient" ? (
        <div className="side-info-card">
          <h3>Hướng dẫn bệnh nhân</h3>
          <p>Trang chủ để khai báo, Kết quả đánh giá để xem nhận xét, video, biểu đồ và frame AI.</p>
          <div className="side-kv"><span>Video của bạn</span><b>{metrics.videos}</b></div>
          <div className="side-kv"><span>Khai báo</span><b>{metrics.symptoms}</b></div>
        </div>
      ) : null}
      {role === "doctor_ktv" ? (
        <div className="side-info-card">
          <h3>Hồ sơ chuyên gia</h3>
          <p>Bác sĩ/KTV theo dõi đánh giá lâm sàng, video và dữ liệu nghiên cứu liên quan.</p>
          <div className="side-kv"><span>Chờ/đã đánh giá</span><b>{metrics.evaluations}</b></div>
          <div className="side-kv"><span>Bệnh nhân</span><b>{metrics.patients}</b></div>
        </div>
      ) : null}
      {role === "researcher" ? (
        <div className="side-info-card">
          <h3>Cấu hình NCV</h3>
          <p>Không gian xem kết quả, frame gallery và dữ liệu trích xuất cho nghiên cứu.</p>
          <div className="side-kv"><span>Dữ liệu NCKH</span><b>{metrics.research_records}</b></div>
          <div className="side-kv"><span>Video AI xong</span><b>{aiVideoDoneCount}</b></div>
        </div>
      ) : null}
      {role === "admin" ? (
        <div className="side-info-card">
          <h3>Quản trị hệ thống</h3>
          <p>Quản trị tài khoản, theo dõi dữ liệu và phản hồi, giữ vai trò cấp quyền cho nhóm nhạy cảm.</p>
          <div className="side-kv"><span>Tài khoản</span><b>{metrics.accounts}</b></div>
          <div className="side-kv"><span>Video</span><b>{metrics.videos}</b></div>
          <div className="side-feature-list">
            <span>Video và đánh giá</span>
            <span>Hồ sơ bệnh nhân</span>
            <span>Khai báo triệu chứng</span>
            <span>Lịch nhắc</span>
            <span>Dữ liệu nghiên cứu</span>
            <span>Audit người dùng</span>
          </div>
        </div>
      ) : null}
      {role !== "patient" ? (
        <div className="side-info-card">
          <h3>Đề tài</h3>
          <p><b>Giảng viên hướng dẫn 1:</b> TS. Trần Hồng Việt</p>
          <p><b>Giảng viên hướng dẫn 2:</b> Nguyễn Thị Thùy Chi</p>
          <p><b>Chủ nhiệm đề tài:</b> Đinh Lê Quỳnh Phương</p>
        </div>
      ) : null}
    </aside>
  );
}

function ThemeToggle({ theme, onToggle }: { theme: ThemeMode; onToggle: () => void }) {
  return (
    <button className="theme-toggle" type="button" onClick={onToggle} title={theme === "dark" ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối"}>
      {theme === "dark" ? <Sun size={17} aria-hidden="true" /> : <Moon size={17} aria-hidden="true" />}
      <span>{theme === "dark" ? "Sáng" : "Tối"}</span>
    </button>
  );
}

function AuthScreen({
  onAuth,
  theme,
  onToggleTheme,
}: {
  onAuth: (auth: AuthResponse) => void;
  theme: ThemeMode;
  onToggleTheme: () => void;
}) {
  const [mode, setMode] = useState<"login" | "register" | "reset">("login");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showRegisterPassword2, setShowRegisterPassword2] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [showResetPassword2, setShowResetPassword2] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [registerForm, setRegisterForm] = useState({
    username: "",
    email: "",
    full_name: "",
    password: "",
    password2: "",
  });
  const [resetForm, setResetForm] = useState({ username: "", email: "", password: "", password2: "" });

  async function submitLogin(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const auth = await api.login(loginForm.username, loginForm.password);
      localStorage.setItem(tokenKey, auth.token);
      onAuth(auth);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể đăng nhập.");
    } finally {
      setLoading(false);
    }
  }

  async function submitRegister(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      await api.register(registerForm);
      const auth = await api.login(registerForm.username, registerForm.password);
      localStorage.setItem(tokenKey, auth.token);
      onAuth(auth);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể đăng ký.");
    } finally {
      setLoading(false);
    }
  }

  async function submitReset(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const result = await api.resetPassword(resetForm);
      setMode("login");
      setLoginForm({ username: resetForm.username, password: "" });
      setResetForm({ username: "", email: "", password: "", password2: "" });
      setMessage(result.message || "Đã đặt lại mật khẩu. Bạn có thể đăng nhập ngay.");
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể khôi phục mật khẩu.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-theme-control">
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
      </div>
      <section className="auth-hero">
        <span className="auth-eyebrow">
          <Shield size={16} aria-hidden="true" />
          Clinical-Grade · Giám sát từ xa bằng Thị giác máy tính
        </span>
        <h1 className="auth-title">
          <span>Giám sát tập</span>
          <em><span>phục hồi</span> <span>chức năng</span></em>
          <span><span>bằng AI,</span> <span>ngay tại nhà.</span></span>
        </h1>
        <p>
          Bệnh nhân khai báo triệu chứng, AI phân tích khung xương và chuyên gia đối chiếu kết quả trong một luồng lâm sàng khép kín.
        </p>
        <div className="auth-stats">
          <div>
            <b>33</b>
            <span>điểm khung xương</span>
          </div>
          <div>
            <b>±15°</b>
            <span>sai số mục tiêu</span>
          </div>
          <div>
            <b>5</b>
            <span>vai trò người dùng</span>
          </div>
        </div>
        <PoseGraphic />
      </section>
      <section className="auth-panel">
        <div className="auth-card-head">
          <div className="brand-mark">
            <HeartPulse size={28} aria-hidden="true" />
          </div>
          <div>
            <h1 className="auth-panel-title">{mode === "login" ? "Đăng nhập hệ thống" : mode === "register" ? "Tạo tài khoản mới" : "Khôi phục mật khẩu"}</h1>
            <p>
              {mode === "login"
                ? "Truy cập bảng điều khiển theo vai trò của bạn."
                : mode === "register"
                  ? "Tài khoản tự đăng ký sẽ được gán vai trò Bệnh nhân."
                  : "Nhập đúng tài khoản và email đã lưu để đặt mật khẩu mới."}
            </p>
          </div>
        </div>
        <div className="segmented" role="tablist" aria-label="Chọn chế độ đăng nhập">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">
            <Lock size={16} aria-hidden="true" />
            Đăng nhập
          </button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")} type="button">
            <UserPlus size={16} aria-hidden="true" />
            Đăng ký
          </button>
        </div>
        {message ? <div className="alert error">{message}</div> : null}
        {mode === "login" ? (
          <form className="form-grid" onSubmit={submitLogin}>
            <label>
              Tài khoản hoặc email
              <span className="input-shell">
                <UserRound size={17} aria-hidden="true" />
                <input
                  value={loginForm.username}
                  onChange={(event) => setLoginForm({ ...loginForm, username: event.target.value })}
                  autoComplete="username"
                  placeholder="bsi01"
                />
              </span>
            </label>
            <label>
              Mật khẩu
              <span className="input-shell">
                <KeyRound size={17} aria-hidden="true" />
                <input
                  type={showLoginPassword ? "text" : "password"}
                  value={loginForm.password}
                  onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
                  autoComplete="current-password"
                  placeholder="••••••••"
                />
                <button
                  className="password-visibility-btn"
                  type="button"
                  aria-label={showLoginPassword ? "An mat khau" : "Hien mat khau"}
                  onClick={() => setShowLoginPassword((value) => !value)}
                >
                  {showLoginPassword ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                </button>
              </span>
            </label>
            <button className="primary-btn" type="submit" disabled={loading}>
              {loading ? <RefreshCw size={18} className="spin" aria-hidden="true" /> : <PlayCircle size={18} aria-hidden="true" />}
              Vào hệ thống
              <ChevronRight size={18} aria-hidden="true" />
            </button>
            <div className="forgot-row">
              <span>Quên mật khẩu?</span>
              <button type="button" onClick={() => setMode("reset")}>
                Khôi phục tại đây
              </button>
            </div>
            <div className="login-role-guides" aria-label="Hướng dẫn đăng nhập theo vai trò">
              <strong>Đăng nhập theo vai trò đã được cấp</strong>
              {loginRoleHints.map((item) => (
                <article key={item.key}>
                  <b>{item.label}</b>
                  <span>{item.text}</span>
                </article>
              ))}
            </div>
          </form>
        ) : mode === "register" ? (
          <form className="form-grid" onSubmit={submitRegister}>
            <label>
              Tài khoản
              <span className="input-shell">
                <UserRound size={17} aria-hidden="true" />
                <input
                  value={registerForm.username}
                  onChange={(event) => setRegisterForm({ ...registerForm, username: event.target.value })}
                  autoComplete="username"
                  placeholder="Chọn tên tài khoản"
                />
              </span>
            </label>
            <label>
              Họ tên
              <span className="input-shell">
                <Users size={17} aria-hidden="true" />
                <input
                  value={registerForm.full_name}
                  onChange={(event) => setRegisterForm({ ...registerForm, full_name: event.target.value })}
                  autoComplete="name"
                  placeholder="VD: Nguyễn Văn A"
                />
              </span>
            </label>
            <label>
              Email
              <span className="input-shell">
                <Mail size={17} aria-hidden="true" />
                <input
                  type="email"
                  value={registerForm.email}
                  onChange={(event) => setRegisterForm({ ...registerForm, email: event.target.value })}
                  autoComplete="email"
                  placeholder="email@huph.edu.vn"
                />
              </span>
            </label>
            <label>
              Mật khẩu
              <span className="input-shell">
                <KeyRound size={17} aria-hidden="true" />
                <input
                  type={showRegisterPassword ? "text" : "password"}
                  value={registerForm.password}
                  onChange={(event) => setRegisterForm({ ...registerForm, password: event.target.value })}
                  autoComplete="new-password"
                  placeholder="••••••••"
                />
                <button
                  className="password-visibility-btn"
                  type="button"
                  aria-label={showRegisterPassword ? "An mat khau" : "Hien mat khau"}
                  onClick={() => setShowRegisterPassword((value) => !value)}
                >
                  {showRegisterPassword ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                </button>
              </span>
            </label>
            <label>
              Xác nhận mật khẩu
              <span className="input-shell">
                <KeyRound size={17} aria-hidden="true" />
                <input
                  type={showRegisterPassword2 ? "text" : "password"}
                  value={registerForm.password2}
                  onChange={(event) => setRegisterForm({ ...registerForm, password2: event.target.value })}
                  autoComplete="new-password"
                  placeholder="••••••••"
                />
                <button
                  className="password-visibility-btn"
                  type="button"
                  aria-label={showRegisterPassword2 ? "An mat khau" : "Hien mat khau"}
                  onClick={() => setShowRegisterPassword2((value) => !value)}
                >
                  {showRegisterPassword2 ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                </button>
              </span>
            </label>
            <button className="primary-btn" type="submit" disabled={loading}>
              {loading ? <RefreshCw size={18} className="spin" aria-hidden="true" /> : <UserPlus size={18} aria-hidden="true" />}
              Tạo tài khoản bệnh nhân
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          </form>
        ) : (
          <form className="form-grid" onSubmit={submitReset}>
            <label>
              Tài khoản
              <span className="input-shell">
                <UserRound size={17} aria-hidden="true" />
                <input
                  value={resetForm.username}
                  onChange={(event) => setResetForm({ ...resetForm, username: event.target.value })}
                  autoComplete="username"
                  placeholder="Tên tài khoản đã có"
                />
              </span>
            </label>
            <label>
              Email đã lưu
              <span className="input-shell">
                <Mail size={17} aria-hidden="true" />
                <input
                  type="email"
                  value={resetForm.email}
                  onChange={(event) => setResetForm({ ...resetForm, email: event.target.value })}
                  autoComplete="email"
                  placeholder="email trong tài khoản"
                />
              </span>
            </label>
            <label>
              Mật khẩu mới
              <span className="input-shell">
                <KeyRound size={17} aria-hidden="true" />
                <input
                  type={showResetPassword ? "text" : "password"}
                  value={resetForm.password}
                  onChange={(event) => setResetForm({ ...resetForm, password: event.target.value })}
                  autoComplete="new-password"
                  placeholder="••••••••"
                />
                <button
                  className="password-visibility-btn"
                  type="button"
                  aria-label={showResetPassword ? "An mat khau" : "Hien mat khau"}
                  onClick={() => setShowResetPassword((value) => !value)}
                >
                  {showResetPassword ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                </button>
              </span>
            </label>
            <label>
              Xác nhận mật khẩu mới
              <span className="input-shell">
                <KeyRound size={17} aria-hidden="true" />
                <input
                  type={showResetPassword2 ? "text" : "password"}
                  value={resetForm.password2}
                  onChange={(event) => setResetForm({ ...resetForm, password2: event.target.value })}
                  autoComplete="new-password"
                  placeholder="••••••••"
                />
                <button
                  className="password-visibility-btn"
                  type="button"
                  aria-label={showResetPassword2 ? "An mat khau" : "Hien mat khau"}
                  onClick={() => setShowResetPassword2((value) => !value)}
                >
                  {showResetPassword2 ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                </button>
              </span>
            </label>
            <button className="primary-btn" type="submit" disabled={loading}>
              {loading ? <RefreshCw size={18} className="spin" aria-hidden="true" /> : <KeyRound size={18} aria-hidden="true" />}
              Đặt lại mật khẩu
              <ChevronRight size={18} aria-hidden="true" />
            </button>
            <div className="forgot-row">
              <span>Đã nhớ mật khẩu?</span>
              <button type="button" onClick={() => setMode("login")}>
                Quay lại đăng nhập
              </button>
            </div>
          </form>
        )}
      </section>
    </main>
  );
}

function Overview({
  payload,
  token,
  onSaved,
  onNavigate,
}: {
  payload: DashboardPayload;
  token: string;
  onSaved: () => void;
  onNavigate: (tab: ViewKey) => void;
}) {
  if (payload.user.role_key === "patient") {
    return <PatientHome payload={payload} token={token} onSaved={onSaved} />;
  }
  if (payload.user.role_key === "doctor_ktv") {
    return <DoctorHome payload={payload} onNavigate={onNavigate} />;
  }
  if (payload.user.role_key === "researcher") {
    return <ResearcherHome payload={payload} onNavigate={onNavigate} />;
  }
  return <AdminHome payload={payload} onNavigate={onNavigate} />;
}

function metricValue(record: Record<string, unknown>, key: string) {
  const metrics = record.metrics && typeof record.metrics === "object" ? (record.metrics as Record<string, unknown>) : {};
  const value = Number(metrics[key] ?? record[key] ?? 0);
  return Number.isFinite(value) ? value : 0;
}

function resultLabelClass(value: unknown) {
  const text = asText(value).toLowerCase();
  if (text.includes("đúng") && !text.includes("gần")) return "pass";
  if (text.includes("gần")) return "near";
  if (text.includes("sai")) return "fail";
  return "";
}

function normalizeVietnameseText(value: unknown) {
  return asText(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function videoPatientName(video: Record<string, unknown>) {
  return asText(video.full_name || video.patient_username || video.username || video.patient || video.patient_name);
}

function videoExerciseName(video: Record<string, unknown>) {
  return asText(video.exercise || video.exercise_name || video.bai_tap || video.video_type || "Chưa rõ bài tập");
}

function evaluationPatientName(record: Record<string, unknown>) {
  return asText(record.patient_username || record.full_name || record.patient_name || record.patient);
}

function evaluationResultKey(value: unknown): "pass" | "near" | "fail" | "unknown" {
  const text = normalizeVietnameseText(value);
  if (text.includes("gan")) return "near";
  if (text.includes("sai") || text.includes("fail")) return "fail";
  if (text.includes("dung") || text.includes("pass") || text.includes("correct")) return "pass";
  return "unknown";
}

function aggregateByLabel(items: string[], fallback = "Chưa rõ") {
  const counts = new Map<string, number>();
  for (const item of items) {
    const label = item && item !== "N/A" ? item : fallback;
    counts.set(label, (counts.get(label) || 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);
}

function exercisePatientDistribution(payload: DashboardPayload) {
  const grouped = new Map<string, Set<string>>();
  for (const video of payload.videos) {
    const exercise = videoExerciseName(video);
    const patient = videoPatientName(video);
    if (!grouped.has(exercise)) grouped.set(exercise, new Set());
    if (patient !== "N/A") grouped.get(exercise)?.add(patient);
  }
  return Array.from(grouped.entries())
    .map(([label, patients]) => ({ label, value: patients.size }))
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value);
}

function exerciseVideoDistribution(payload: DashboardPayload) {
  return aggregateByLabel(payload.videos.map(videoExerciseName));
}

function evaluationResultDistribution(payload: DashboardPayload) {
  const initial = {
    pass: { label: "Đúng", value: 0 },
    near: { label: "Gần đúng", value: 0 },
    fail: { label: "Sai", value: 0 },
    unknown: { label: "Chưa rõ", value: 0 },
  };
  for (const record of payload.evaluations) {
    const key = evaluationResultKey(record.doctor_result || record.result || record.status);
    initial[key].value += 1;
  }
  return [initial.pass, initial.near, initial.fail, initial.unknown].filter((item) => item.value > 0);
}

function frameTotalsFromVideos(videos: Record<string, unknown>[]): ResearcherFrameTotals {
  return videos.reduce<ResearcherFrameTotals>(
    (sum, video) => {
      const pass = metricValue(video, "frame_dung");
      const near = metricValue(video, "frame_gan_dung");
      const fail = metricValue(video, "frame_sai");
      const unknown = metricValue(video, "frame_khong_nhan_dang") || metricValue(video, "unknown_frames") || metricValue(video, "ml_frame_unknown");
      const total = metricValue(video, "tong_frame_da_cham") || metricValue(video, "tong_frame") || metricValue(video, "ml_tong_frame") || pass + near + fail + unknown;
      return {
        pass: sum.pass + pass,
        near: sum.near + near,
        fail: sum.fail + fail,
        unknown: sum.unknown + unknown,
        total: sum.total + total,
      };
    },
    { pass: 0, near: 0, fail: 0, unknown: 0, total: 0 },
  );
}

function frameDistribution(totals: ResearcherFrameTotals) {
  return [
    { key: "pass", label: "Đúng", value: totals.pass, color: "#16a34a" },
    { key: "near", label: "Gần đúng", value: totals.near, color: "#0284c7" },
    { key: "fail", label: "Sai", value: totals.fail, color: "#dc2626" },
    { key: "unknown", label: "Không nhận dạng", value: totals.unknown, color: "#64748b" },
  ].filter((item) => item.value > 0);
}

function averageVideoAccuracy(videos: Record<string, unknown>[]) {
  const values = videos
    .map((video) => Number(video.accuracy) || metricValue(video, "do_chinh_xac") || metricValue(video, "ty_le_tong_the"))
    .filter((value) => Number.isFinite(value) && value > 0);
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

type ResearcherFrameTotals = {
  pass: number;
  near: number;
  fail: number;
  unknown: number;
  total: number;
};

function AdminHome({ payload, onNavigate }: { payload: DashboardPayload; onNavigate: (tab: ViewKey) => void }) {
  const metrics = payload.metrics;
  const aiVideoDoneCount = researcherAiVideoCount(payload);
  const totals = frameTotalsFromVideos(payload.videos);
  const frameChart = frameDistribution(totals).map((item) => ({ label: item.label, value: item.value }));
  const exercisePatients = exercisePatientDistribution(payload);
  const resultDist = evaluationResultDistribution(payload);
  const patientCount = new Set(payload.videos.map(videoPatientName).filter((name) => name !== "N/A")).size || metrics.patients;
  const avgAccuracy = averageVideoAccuracy(payload.videos);
  const passRate = totals.total ? (totals.pass / totals.total) * 100 : 0;
  const cards = [
    { icon: Users, label: "Bệnh nhân", value: patientCount, hint: `${metrics.accounts} tài khoản hệ thống` },
    { icon: Video, label: "Video AI xong", value: aiVideoDoneCount, hint: `${metrics.videos || payload.videos.length} video trong scope` },
    { icon: ClipboardList, label: "Phiếu đánh giá", value: metrics.evaluations, hint: `${metrics.research_records} bản ghi NCKH` },
    { icon: BarChart3, label: "Accuracy TB", value: `${fmtMetric(avgAccuracy, 1)}%`, hint: `${fmtMetric(passRate, 1)}% frame đúng` },
  ];
  return (
    <section className="workspace-section admin-home">
      <section className="role-home-hero admin">
        <div>
          <span className="role-pill admin">Quản trị viên - live system overview</span>
          <h1>Bảng điều phối hệ thống Rehab AI Monitor</h1>
          <p>Theo dõi tài khoản, video, phiếu nghiên cứu, triệu chứng và chất lượng AI bằng các chỉ số tự động từ dữ liệu local.</p>
        </div>
        <DynamicMetricStrip items={cards} />
      </section>

      <div className="analytics-grid">
        <section className="panel dynamic-chart-panel">
          <div className="panel-title">
            <Users size={18} aria-hidden="true" />
            <h2>Số bệnh nhân theo bài tập</h2>
          </div>
          <MiniBarChart data={exercisePatients.length ? exercisePatients : exerciseVideoDistribution(payload)} />
        </section>
        <section className="panel dynamic-chart-panel">
          <div className="panel-title">
            <ClipboardList size={18} aria-hidden="true" />
            <h2>Phân bố kết quả đánh giá</h2>
          </div>
          <ResultDistributionChart data={resultDist.map((item) => ({ label: item.label, value: item.value }))} centerMode="total" />
        </section>
        <section className="panel dynamic-chart-panel">
          <div className="panel-title">
            <Activity size={18} aria-hidden="true" />
            <h2>Frame AI Đúng / Gần đúng / Sai</h2>
          </div>
          <MiniBarChart data={frameChart} />
        </section>
        <section className="panel dynamic-chart-panel">
          <div className="panel-title">
            <Database size={18} aria-hidden="true" />
            <h2>Điều phối nhanh</h2>
          </div>
          <div className="quick-stat-list">
            <button type="button" onClick={() => onNavigate("admin_panel")}>
              <Settings size={17} aria-hidden="true" />
              <span>Quản lý tài khoản</span>
              <b>{metrics.accounts}</b>
            </button>
            <button type="button" onClick={() => onNavigate("evaluation_forms")}>
              <ClipboardList size={17} aria-hidden="true" />
              <span>Phiếu đánh giá</span>
              <b>{metrics.evaluations}</b>
            </button>
            <button type="button" onClick={() => onNavigate("admin_research")}>
              <FlaskConical size={17} aria-hidden="true" />
              <span>Dữ liệu NCKH</span>
              <b>{metrics.research_records}</b>
            </button>
          </div>
        </section>
      </div>
    </section>
  );
}

function ResearcherHome({ payload, onNavigate }: { payload: DashboardPayload; onNavigate: (tab: ViewKey) => void }) {
  const metrics = payload.metrics;
  const aiVideoDoneCount = researcherAiVideoCount(payload);
  const aiEvaluations = payload.evaluations.filter((record) => asText(record.source).includes("video_list_ai_researcher"));
  const latestAiVideos = payload.videos.filter((video) => asText(video.latest_bundle_updated_at) !== "N/A").slice(0, 8);
  const sourceVideos = latestAiVideos.length ? latestAiVideos : payload.videos.slice(0, 8);
  const exercisePatients = exercisePatientDistribution(payload);
  const totals = frameTotalsFromVideos(sourceVideos);
  const patientCount = new Set(payload.videos.map((video) => asText(video.full_name || video.patient_username || video.username)).filter((name) => name !== "N/A")).size;
  const avgAccuracy = averageVideoAccuracy(sourceVideos);
  const passRate = totals.total ? (totals.pass / totals.total) * 100 : 0;
  const unknownRate = totals.total ? (totals.unknown / totals.total) * 100 : 0;
  const distribution: { key: string; label: string; value: number; color: string }[] = [
    { key: "pass", label: "PASS", value: totals.pass, color: "#16a34a" },
    { key: "near", label: "NEAR", value: totals.near, color: "#0284c7" },
    { key: "fail", label: "FAIL", value: totals.fail, color: "#dc2626" },
    { key: "unknown", label: "UNKNOWN", value: totals.unknown, color: "#64748b" },
  ];
  const denominator = totals.total || distribution.reduce((sum, item) => sum + item.value, 0) || 1;
  const latestRows = sourceVideos.slice(0, 6).map((video) => {
    const evaluation = aiEvaluations.find((item) => asText(item.video_name) === asText(video.video_name));
    return {
      patient: video.full_name || video.patient_username || video.username,
      video: video.video_name,
      result: evaluation?.doctor_result || video.status || "N/A",
      accuracy: `${fmtMetric(video.accuracy || metricValue(video, "do_chinh_xac"), 2)}%`,
      frames: `${fmtInt(metricValue(video, "frame_dung"))}/${fmtInt(metricValue(video, "tong_frame_da_cham") || metricValue(video, "tong_frame"))}`,
      time: video.time,
      className: resultLabelClass(evaluation?.doctor_result || video.status),
    };
  });
  const pipelineItems = [
    { icon: Upload, title: "Thu nhận video", text: `${metrics.videos} video từ bệnh nhân và dữ liệu local` },
    { icon: Target, title: "Chấm frame AI", text: `${fmtInt(totals.total)} frame đang có trong nhóm mới nhất` },
    { icon: BarChart3, title: "Biểu đồ nghiên cứu", text: "Góc khớp, histogram, boxplot, radar chỉ số" },
    { icon: ClipboardList, title: "Phiếu NCV/AI", text: `${aiEvaluations.length} phiếu tự động đồng bộ từ video_list` },
  ];

  return (
    <section className="workspace-section researcher-home">
      <section className="researcher-hero">
        <div className="researcher-hero-copy">
          <span className="role-pill researcher">Nghiên cứu viên - AI clinical monitor</span>
          <h1>Trung tâm điều phối dữ liệu vận động và kết quả NCV/AI</h1>
          <p>
            Theo dõi video, frame AI, biểu đồ góc khớp và phiếu nghiên cứu từ một dashboard duy nhất. Dữ liệu hiển thị
            được đồng bộ trực tiếp từ `video_list.json`, `latest_video_bundle.json` và `doctor_evaluations.json`.
          </p>
          <div className="researcher-hero-actions">
            <button className="primary-btn" type="button" onClick={() => onNavigate("research_analysis")}>
              <BarChart3 size={18} aria-hidden="true" />
              Mở phân tích AI
            </button>
            <button className="ghost-btn" type="button" onClick={() => onNavigate("evaluation_forms")}>
              <ClipboardList size={18} aria-hidden="true" />
              Mở phiếu NCV/AI
            </button>
          </div>
        </div>
        <div className="researcher-command-panel" aria-label="Tóm tắt dữ liệu NCV">
          <div>
            <span>Video AI xong</span>
            <strong>{aiVideoDoneCount}</strong>
          </div>
          <div>
            <span>Bệnh nhân</span>
            <strong>{patientCount}</strong>
          </div>
          <div>
            <span>Accuracy TB</span>
            <strong>{fmtMetric(avgAccuracy, 1)}%</strong>
          </div>
          <div>
            <span>PASS rate</span>
            <strong>{fmtMetric(passRate, 1)}%</strong>
          </div>
        </div>
      </section>

      <div className="researcher-kpi-grid">
        <StatCard icon={Database} label="Dữ liệu NCKH" value={metrics.research_records} hint={`${metrics.training_sessions} phiên tập`} />
        <StatCard icon={Video} label="Video trong scope" value={metrics.videos} hint={`${latestAiVideos.length || sourceVideos.length} video mới nhất`} />
        <StatCard icon={ClipboardList} label="Phiếu đánh giá" value={metrics.evaluations} hint={`${aiEvaluations.length} phiếu AI tự động`} />
        <StatCard icon={AlertCircle} label="UNKNOWN" value={fmtInt(totals.unknown)} hint={`${fmtMetric(unknownRate, 1)}% tổng frame mới`} />
      </div>

      <section className="researcher-pipeline">
        {pipelineItems.map(({ icon: Icon, title, text }) => (
          <article key={title}>
            <Icon size={20} aria-hidden="true" />
            <div>
              <strong>{title}</strong>
              <span>{text}</span>
            </div>
          </article>
        ))}
      </section>

      <div className="researcher-dashboard-grid">
        <section className="panel researcher-chart-panel">
          <div className="panel-title">
            <BarChart3 size={18} aria-hidden="true" />
            <h2>Phân bố frame mới nhất</h2>
          </div>
          <div className="researcher-distribution">
            {distribution.map((item) => (
              <div key={item.key}>
                <span>
                  <i style={{ background: item.color }} aria-hidden="true" />
                  {item.label}
                </span>
                <b>{fmtInt(item.value)}</b>
                <div className="researcher-bar" aria-hidden="true">
                  <em style={{ width: `${Math.max(2, (item.value / denominator) * 100)}%`, background: item.color }} />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel researcher-chart-panel">
          <div className="panel-title">
            <Target size={18} aria-hidden="true" />
            <h2>Bệnh nhân theo bài tập</h2>
          </div>
          <MiniBarChart data={exercisePatients.length ? exercisePatients : exerciseVideoDistribution(payload)} />
        </section>

        <section className="panel researcher-latest-panel">
          <div className="panel-title with-search">
            <div>
              <Microscope size={18} aria-hidden="true" />
              <h2>Video AI mới nhất</h2>
            </div>
            <span className="role-pill researcher">{sourceVideos.length} video</span>
          </div>
          <div className="researcher-video-list">
            {latestRows.map((row, index) => (
              <article key={`${row.video}-${index}`}>
                <div>
                  <b>{asText(row.patient)}</b>
                  <span>{compactText(row.video, 88)}</span>
                </div>
                <strong className={row.className}>{asText(row.result)}</strong>
                <small>{row.accuracy} | {row.frames} frame | {asText(row.time)}</small>
              </article>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}

function DoctorHome({ payload, onNavigate }: { payload: DashboardPayload; onNavigate: (tab: ViewKey) => void }) {
  const latestVideos = payload.videos.slice(0, 8);
  const latestSymptoms = payload.symptoms.slice(0, 3);
  const exercisePatients = exercisePatientDistribution(payload);
  const resultDist = evaluationResultDistribution(payload);
  const aiVideoDoneCount = researcherAiVideoCount(payload);
  const doctorCards = [
    { icon: Users, label: "Bệnh nhân", value: payload.metrics.patients, hint: `${payload.metrics.symptoms} khai báo triệu chứng` },
    { icon: Video, label: "Video theo dõi", value: payload.metrics.videos, hint: `${aiVideoDoneCount} video có AI` },
    { icon: ClipboardList, label: "Phiếu đánh giá", value: payload.metrics.evaluations, hint: `${payload.metrics.research_records} phiếu NCKH` },
    { icon: Activity, label: "Lịch nhắc", value: payload.metrics.schedules, hint: "Theo dõi tập tại nhà" },
  ];
  return (
    <section className="workspace-section doctor-home">
      <section className="doctor-hero role-home-hero doctor">
        <div>
          <span className="role-pill doctor">Không gian Bác sĩ / KTV PHCN</span>
          <h1>Theo dõi tập phục hồi chức năng tại nhà bằng dữ liệu video và nhận xét lâm sàng.</h1>
          <p>
            Bác sĩ/KTV đối chiếu video bệnh nhân tải lên, xem kết quả AI từ NCV, hoàn thiện phiếu PHCN/NCKH và gửi khuyến nghị lại cho bệnh nhân trong một luồng kín.
          </p>
        </div>
        <div className="doctor-hero-actions">
          <button type="button" className="primary-btn" onClick={() => onNavigate("evaluation_forms")}>
            <ClipboardList size={18} aria-hidden="true" />
            Mở phiếu đánh giá
          </button>
          <button type="button" className="ghost-btn" onClick={() => onNavigate("evaluation_forms")}>
            <Video size={18} aria-hidden="true" />
            Video trong phiếu
          </button>
          <button type="button" className="ghost-btn" onClick={() => onNavigate("patient_schedule")}>
            <Activity size={18} aria-hidden="true" />
            Tạo lịch nhắc
          </button>
        </div>
      </section>
      <DynamicMetricStrip items={doctorCards} tone="light" />

      <div className="doctor-insight-grid">
        <article>
          <span>01</span>
          <h3>Bối cảnh PHCN tại Việt Nam</h3>
          <p>Nhu cầu phục hồi chức năng tăng nhanh, trong khi người bệnh sau xuất viện thường cần tiếp tục tập tại nhà và cần chuyên gia theo dõi an toàn.</p>
        </article>
        <article>
          <span>02</span>
          <h3>Vai trò bác sĩ/KTV</h3>
          <p>Đánh giá tư thế, biên độ, nhịp tập, mức đau và mức an toàn; từ đó đưa ra kế hoạch tập tiếp hoặc tái đánh giá.</p>
        </article>
        <article>
          <span>03</span>
          <h3>Hệ thống Rehab AI Monitor</h3>
          <p>Video thô, khung xương AI, biểu đồ nghiên cứu và nhận xét chuyên môn được đặt cạnh nhau để quyết định lâm sàng dễ hơn.</p>
        </article>
      </div>

      <div className="analytics-grid">
        <section className="panel dynamic-chart-panel">
          <div className="panel-title">
            <Target size={18} aria-hidden="true" />
            <h2>Bệnh nhân theo bài tập</h2>
          </div>
          <MiniBarChart data={exercisePatients.length ? exercisePatients : exerciseVideoDistribution(payload)} />
        </section>
        <section className="panel dynamic-chart-panel">
          <div className="panel-title">
            <BarChart3 size={18} aria-hidden="true" />
            <h2>Kết quả đúng / gần đúng / sai</h2>
          </div>
          <ResultDistributionChart data={resultDist.map((item) => ({ label: item.label, value: item.value }))} centerMode="total" />
        </section>
      </div>

      <div className="panel-grid">
        <section className="panel">
          <div className="panel-title">
            <Video size={18} aria-hidden="true" />
            <h2>Video cần theo dõi gần đây</h2>
          </div>
          <DataTable
            rows={latestVideos}
            empty="Chưa có video bệnh nhân trong phạm vi tài khoản."
            columns={[
              { key: "full_name", label: "Người bệnh" },
              { key: "video_name", label: "Video", wide: true },
              { key: "exercise", label: "Bài tập" },
              { key: "status", label: "Trạng thái" },
            ]}
          />
        </section>
        <section className="panel">
          <div className="panel-title">
            <HeartPulse size={18} aria-hidden="true" />
            <h2>Khai báo triệu chứng mới</h2>
          </div>
          <DataTable
            rows={latestSymptoms}
            empty="Chưa có khai báo triệu chứng."
            columns={[
              { key: "full_name", label: "Bệnh nhân" },
              { key: "vas", label: "VAS" },
              { key: "exercise", label: "Bài tập" },
              { key: "symptoms", label: "Triệu chứng", wide: true },
            ]}
          />
        </section>
      </div>
    </section>
  );
}

function youtubeEmbedUrl(url: string) {
  const match = url.match(/(?:youtu\.be\/|v=)([A-Za-z0-9_-]+)/);
  return match ? `https://www.youtube.com/embed/${match[1]}` : url;
}

function PatientHome({ payload, token, onSaved }: { payload: DashboardPayload; token: string; onSaved: () => void }) {
  const [selected, setSelected] = useState(exerciseGuides[0].key);
  const guide = exerciseGuides.find((item) => item.key === selected) || exerciseGuides[0];
  const recentEvaluations = payload.evaluations.slice(0, 3);
  const recentVideos = (payload.videos?.length ? payload.videos : payload.latest_evaluated_videos).slice(0, 3);

  return (
    <section className="workspace-section patient-home">
      <section className="patient-hero-panel">
        <div>
          <span className="role-pill patient">Không gian bệnh nhân</span>
          <h1>Hôm nay tập vai an toàn hơn, có chuyên gia theo dõi phía sau.</h1>
          <p>
            Chọn bài tập, xem video mẫu, khai báo triệu chứng và theo dõi nhận xét đã gửi từ bác sĩ/KTV hoặc NCV.
          </p>
        </div>
        <div className="patient-hero-metrics" aria-label="Tóm tắt bệnh nhân">
          <span><b>{payload.metrics.videos}</b> video đã gửi</span>
          <span><b>{payload.metrics.evaluations}</b> nhận xét</span>
          <span><b>{payload.metrics.schedules}</b> lịch nhắc</span>
        </div>
      </section>

      <div className="patient-guide-layout">
        <section className="panel exercise-selector-panel">
          <div className="panel-title">
            <Target size={18} aria-hidden="true" />
            <h2>Chọn bài tập và xem hướng dẫn</h2>
          </div>
          <div className="exercise-tabs">
            {exerciseGuides.map((item) => (
              <button key={item.key} className={item.key === selected ? "active" : ""} type="button" onClick={() => setSelected(item.key)}>
                <span>{item.icon}</span>
                {item.name}
              </button>
            ))}
          </div>
          <article className="exercise-guide-card">
            <div>
              <span className="guide-kicker">{guide.duration}s/lần · {guide.reps} lần/ngày</span>
              <h3>{guide.name}</h3>
              <p>{guide.description}</p>
            </div>
            <div className="guide-columns">
              <div>
                <h4>Hướng dẫn tập luyện</h4>
                <ol>
                  {guide.steps.map((step) => <li key={step}>{step}</li>)}
                </ol>
              </div>
              <div>
                <h4>Lợi ích</h4>
                <ul>
                  {guide.benefits.map((benefit) => <li key={benefit}>{benefit}</li>)}
                </ul>
                <h4>Lưu ý an toàn</h4>
                <ul>
                  {guide.cautions.map((caution) => <li key={caution}>{caution}</li>)}
                </ul>
              </div>
            </div>
          </article>
        </section>

        <section className="panel youtube-panel">
          <div className="panel-title">
            <PlayCircle size={18} aria-hidden="true" />
            <h2>Video YouTube tham khảo</h2>
          </div>
          <iframe
            title={`Video hướng dẫn ${guide.name}`}
            src={youtubeEmbedUrl(guide.youtube)}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
          <a href={guide.youtube} target="_blank" rel="noreferrer" className="secondary-link">
            <LinkIcon size={15} aria-hidden="true" />
            Mở video mẫu
          </a>
        </section>
      </div>

      <div className="panel-grid">
        <PatientSymptomForm token={token} onSaved={onSaved} />
        <PatientVideoUpload token={token} onSaved={onSaved} />
        <section className="panel upload-ready-panel">
          <div className="panel-title">
            <Upload size={18} aria-hidden="true" />
            <h2>Tải lên video tập luyện</h2>
          </div>
          <div className="upload-dropzone">
            <Upload size={28} aria-hidden="true" />
            <strong>Gửi video bài tập mới cho bác sĩ/KTV và NCV</strong>
            <span>React UI hiện dùng backend đọc dữ liệu hiện có; endpoint upload thật sẽ được nối ở bước tiếp theo.</span>
          </div>
        </section>
        <section className="panel">
          <div className="panel-title">
            <ClipboardList size={18} aria-hidden="true" />
            <h2>Nhận xét mới nhất</h2>
          </div>
          <div className="patient-note-list">
            {recentEvaluations.map((evaluation, index) => (
              <article key={`${evaluation.time || index}`}>
                <b>{asText(evaluation.doctor_result)}</b>
                <span>{asText(evaluation.doctor_name || evaluation.doctor_username)} · {asText(evaluation.time)}</span>
                <p>{compactText(evaluation.comments || evaluation.plan, 180)}</p>
              </article>
            ))}
            {!recentEvaluations.length ? <div className="empty-state">Chưa có nhận xét được gửi cho bạn.</div> : null}
          </div>
        </section>
        <section className="panel wide-panel">
          <div className="panel-title">
            <Video size={18} aria-hidden="true" />
            <h2>Kết quả/video gần đây của bạn</h2>
          </div>
          <DataTable
            rows={recentVideos}
            empty="Chưa có video trong tài khoản bệnh nhân."
            columns={[
              { key: "video_name", label: "Video", wide: true },
              { key: "exercise", label: "Bài tập" },
              { key: "accuracy", label: "AI" },
              { key: "status", label: "Trạng thái" },
            ]}
          />
        </section>
      </div>
    </section>
  );
}

function VideoView({ payload }: { payload: DashboardPayload }) {
  return (
    <section className="workspace-section">
      <div className="panel-title page-line">
        <Video size={18} aria-hidden="true" />
        <h2>Video và kết quả AI</h2>
      </div>
      <DataTable
        rows={payload.videos}
        empty="Chưa có video."
        columns={[
          { key: "full_name", label: "Người bệnh" },
          { key: "video_name", label: "Video", wide: true },
          { key: "exercise", label: "Bài tập" },
          { key: "accuracy", label: "AI" },
          { key: "status", label: "Trạng thái" },
          { key: "time", label: "Thời gian" },
        ]}
      />
    </section>
  );
}

function VideoResultWorkspace({
  payload,
  token,
  title,
  controls,
}: {
  payload: DashboardPayload;
  token: string;
  title: string;
  controls?: (video: Record<string, unknown>, detail: VideoDetailPayload | null, reload: () => void) => ReactNode;
}) {
  const [selectedId, setSelectedId] = useState<number>(() => 0);
  const [detail, setDetail] = useState<VideoDetailPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [resultSubtab, setResultSubtab] = useState<"charts" | "media">("charts");
  const [mediaIssue, setMediaIssue] = useState("");
  const [frameOffset, setFrameOffset] = useState(0);
  const [zoomFrame, setZoomFrame] = useState<VideoDetailPayload["frames"][number] | null>(null);
  const [framePhase, setFramePhase] = useState("all");
  const [frameStatus, setFrameStatus] = useState("ALL");
  const frameLimit = 16;
  const videos = payload.videos?.length ? payload.videos : payload.latest_evaluated_videos;
  const detailCache = useRef(new Map<string, VideoDetailPayload>());
  const effectiveFrameLimit = resultSubtab === "media" ? frameLimit : 1;
  const includeChart = resultSubtab === "charts";

  useEffect(() => {
    if (!videos.length) {
      setDetail(null);
      return;
    }
    const nextId = Math.min(selectedId, videos.length - 1);
    const selectedVideo = videos[nextId] || {};
    const detailId = selectedVideo._detail_id ?? nextId;
    const cacheKey = `${detailId}:${frameOffset}:${effectiveFrameLimit}:${framePhase}:${frameStatus}:${includeChart}`;
    const cached = detailCache.current.get(cacheKey);
    if (cached) {
      setDetail(cached);
      setLoading(false);
      setMessage("");
      setMediaIssue("");
      return;
    }
    setLoading(true);
    setMessage("");
    setMediaIssue("");
    api
      .videoDetail(token, String(detailId), frameOffset, effectiveFrameLimit, framePhase, frameStatus, includeChart)
      .then((data) => {
        detailCache.current.set(cacheKey, data);
        setDetail(data);
      })
      .catch((error) => {
        setDetail(null);
        setMessage(error instanceof ApiError ? error.message : "Không thể tải chi tiết video.");
      })
      .finally(() => setLoading(false));
  }, [selectedId, token, videos.length, frameOffset, framePhase, frameStatus, effectiveFrameLimit, includeChart]);

  useEffect(() => {
    setFrameOffset(0);
  }, [framePhase, frameStatus]);

  const latest = detail?.latest_evaluation;
  const selectedVideo = videos[Math.min(selectedId, Math.max(0, videos.length - 1))] || {};
  const analysisControls = controls;
  const reloadDetail = () => {
    const detailId = selectedVideo._detail_id ?? selectedId;
    if (!videos.length) return;
    setLoading(true);
    api
      .videoDetail(token, String(detailId), frameOffset, effectiveFrameLimit, framePhase, frameStatus, includeChart)
      .then((data) => {
        detailCache.current.clear();
        detailCache.current.set(`${detailId}:${frameOffset}:${effectiveFrameLimit}:${framePhase}:${frameStatus}:${includeChart}`, data);
        setDetail(data);
      })
      .catch((error) => setMessage(error instanceof ApiError ? error.message : "Không thể tải chi tiết video."))
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    // Progress is polled by AnalysisJobControls via the lightweight job endpoint.
    // Avoid reloading full video detail + 48 frame images during analysis; that
    // competes with MediaPipe and makes the job look frozen.
    return undefined;
  }, [detail?.latest_job?.status, detail?.latest_job?.run_id, selectedId, frameOffset, framePhase, frameStatus]);
  const frameStart = detail?.frame_offset || 0;
  const frameTotal = detail?.frame_total || 0;
  const frameEnd = Math.min(frameTotal, frameStart + (detail?.frames.length || 0));
  const canPrevFrames = frameStart > 0;
  const canNextFrames = frameEnd < frameTotal;
  const framePage = frameTotal ? Math.floor(frameStart / frameLimit) + 1 : 0;
  const framePages = frameTotal ? Math.ceil(frameTotal / frameLimit) : 0;
  const previewImage = detail?.media.preview_image_url || detail?.frames.find((frame) => frame.image_url)?.image_url || "";
  const playbackBlocked = detail?.media.playback_status === "unreadable_video";
  const playbackRebuilt = detail?.media.playback_status === "rebuilt_from_frames";
  const playbackUnverified = detail?.media.playback_status === "fallback_unverified";
  const researchMetrics = detail?.chart.research_metrics || {};
  const metricNumber = (key: string) => {
    const value = Number(researchMetrics[key]);
    return Number.isFinite(value) ? value : null;
  };
  const passFrames = metricNumber("pass_frames") || 0;
  const nearFrames = metricNumber("near_frames") || 0;
  const failFrames = metricNumber("fail_frames") || 0;
  const unknownFrames = metricNumber("unknown_frames") || 0;
  const recognizedFrames = passFrames + nearFrames + failFrames;
  const totalMetricFrames = metricNumber("total_frames") || frameTotal || detail?.frame_total || detail?.frames.length || 0;
  const accuracyMetric = metricNumber("accuracy") ?? Number(detail?.video.accuracy ?? NaN);
  const f1Metric = metricNumber("f1_score");
  const maeMetric = metricNumber("mae");
  const iccMetric = metricNumber("icc");
  const selectedExerciseKey = detailExerciseKey(detail);
  const showCodmanPhaseStrip = selectedExerciseKey === "codman";
  const moveFramePage = (direction: -1 | 1) => {
    setFrameOffset((current) => {
      const maxOffset = Math.max(0, frameTotal - frameLimit);
      return Math.min(maxOffset, Math.max(0, current + direction * frameLimit));
    });
  };
  const goFramePage = (page: number) => {
    const safePage = Math.min(Math.max(1, page), Math.max(1, framePages));
    setFrameOffset((safePage - 1) * frameLimit);
  };

  return (
    <section className="workspace-section">
      <div className="panel-title page-line">
        <Video size={18} aria-hidden="true" />
        <h2>{title}</h2>
      </div>
      {analysisControls ? analysisControls(selectedVideo, detail, reloadDetail) : null}
      <div className="result-layout">
        <section className="panel video-picker">
          <div className="panel-title">
            <ClipboardList size={18} aria-hidden="true" />
            <h2>Danh sách video</h2>
          </div>
          <div className="video-list">
            {videos.map((video, index) => (
              <button
                key={`${video._detail_id || index}-${video.video_name || index}`}
                className={selectedId === index ? "active" : ""}
                onClick={() => {
                  setSelectedId(index);
                  setFrameOffset(0);
                  setFramePhase("all");
                  setFrameStatus("ALL");
                }}
                type="button"
              >
                <b>{compactText(video.video_name, 64)}</b>
                <span className="video-group-line">{compactText(video._group_patient || video.full_name || video.username, 48)} · {compactText(video._group_exercise || video.exercise, 48)}</span>
                <span>{compactText(video.full_name || video.username, 48)} · {compactText(video.exercise, 48)}</span>
                <small>{asText(video.status)} · AI {asText(video.accuracy)}</small>
                <span className="artifact-badges">
                  <i className={video._has_video_file ? "on" : ""}>Video</i>
                  <i className={video._has_chart ? "on" : ""}>Biểu đồ</i>
                  <i className={video._has_frames ? "on" : ""}>{video._has_frames ? "Khung xương" : "Preview"}</i>
                </span>
              </button>
            ))}
            {!videos.length ? <div className="empty-state">Chưa có video trong phạm vi tài khoản.</div> : null}
          </div>
        </section>
        <section className="panel result-detail">
          {loading ? <div className="empty-state">Đang tải chi tiết video...</div> : null}
          {message ? <div className="alert error">{message}</div> : null}
          {detail ? (
            <>
              <div className="result-head">
                <div>
                  <h2>{asText(detail.video.video_name)}</h2>
                  <p>{asText(detail.video.full_name || detail.video.username)} · {asText(detail.video.exercise)}</p>
                </div>
                <span className="role-pill">{asText(detail.video.status)}</span>
              </div>
              {showCodmanPhaseStrip && detail.chart.phases?.length ? (
                <div className="phase-strip">
                  {detail.chart.phases.map((phase) => (
                    <span key={phase.label}>
                      <b>{phase.label}</b>
                      {phase.value.toFixed(1)}%
                    </span>
                  ))}
                </div>
              ) : null}
              <div className="result-summary">
                <StatCard icon={BarChart3} label="Accuracy AI" value={Number.isFinite(accuracyMetric) ? fmtMetric(accuracyMetric, 2) : "N/A"} hint="Đồng bộ theo biểu đồ/video/frames" />
                <StatCard icon={FileText} label="Đánh giá" value={detail.evaluations.length} hint={latest ? asText(latest.doctor_result) : "Chưa có"} />
                <StatCard icon={Download} label="Frames" value={fmtInt(recognizedFrames || totalMetricFrames)} hint={recognizedFrames ? "Có khung xương AI" : detail.media.frame_data_exists ? "Có dữ liệu frame AI" : "Preview từ video"} />
                <StatCard icon={AlertCircle} label="UNKNOWN" value={fmtInt(unknownFrames)} hint="Không nhận dạng/lẫn người" />
              </div>
              <section className="ml-status-strip" aria-label="Thông tin ML">
                <div>
                  <span>Model/job</span>
                  <strong>{asText(detail.latest_job?.job_meta?.options?.model_type || detail.latest_job?.status || "Chưa có job mới")}</strong>
                </div>
                <div>
                  <span>Accuracy</span>
                  <strong>{Number.isFinite(accuracyMetric) ? fmtMetric(accuracyMetric, 2) : "N/A"}</strong>
                </div>
                <div>
                  <span>F1-score</span>
                  <strong>{f1Metric !== null ? fmtMetric(f1Metric, 3) : "N/A"}</strong>
                </div>
                <div>
                  <span>MAE / ICC</span>
                  <strong>{maeMetric !== null ? fmtMetric(maeMetric, 3) : "N/A"} / {iccMetric !== null ? fmtMetric(iccMetric, 3) : "N/A"}</strong>
                </div>
              </section>
              {!detail.media.analysis_artifact_exists ? (
                <div className="alert warning">
                  Video này chưa có CSV/frame khung xương AI trong dữ liệu local; hệ thống đang hiển thị preview lấy trực tiếp từ video gốc.
                </div>
              ) : null}
              <div className="result-subtabs" role="tablist" aria-label="Kết quả video">
                <button className={resultSubtab === "charts" ? "active" : ""} onClick={() => setResultSubtab("charts")} type="button">
                  <BarChart3 size={16} aria-hidden="true" />
                  Kết quả biểu đồ
                </button>
                <button className={resultSubtab === "media" ? "active" : ""} onClick={() => setResultSubtab("media")} type="button">
                  <Video size={16} aria-hidden="true" />
                  Video & Frames
                </button>
              </div>
              {resultSubtab === "media" ? (
                <section className="result-card video-preview-card">
                  <h3>Video</h3>
                  {mediaIssue ? <div className="alert error">{mediaIssue}</div> : null}
                  {playbackBlocked ? (
                    <div className="alert warning">
                      File video local hiện không đọc được, nên hệ thống đang hiển thị frame preview từ artifact phân tích.
                    </div>
                  ) : null}
                  {playbackRebuilt ? (
                    <div className="alert success">
                      Video local bi hong container; he thong da dung lai ban H.264 tu frames da trich xuat.
                    </div>
                  ) : null}
                  {playbackUnverified ? (
                    <div className="alert warning">
                      Video nay chua co ban H.264 chac chan; he thong se hien thi frame preview tu artifact thay vi giu player den.
                    </div>
                  ) : null}
                  {false && playbackUnverified ? (
                    <div className="alert warning">
                      Video này chưa có bản H.264 chắc chắn; nếu trình duyệt hiện màn đen, hãy dùng video gốc dự phòng hoặc xem frame bên dưới.
                    </div>
                  ) : null}
                  {detail.media.video_url && !playbackBlocked && !playbackUnverified ? (
                    <>
                      <PhaseVideoPlayer
                        detail={detail}
                        mediaKey={String(detail.media.video_path || detail.media.video_url || detail.video.video_name || "")}
                        poster={previewImage ? mediaUrl(previewImage) : undefined}
                        src={mediaUrl(detail.media.video_url)}
                        portrait={["codman", "pulley"].includes(detailExerciseKey(detail))}
                        displayRotation={Number(detail.media.display_rotation || 0)}
                        onPhaseChange={(value) => {
                          setFrameOffset(0);
                          setFramePhase(value);
                        }}
                        onError={() => setMediaIssue("Video này browser chưa phát được trực tiếp; frame preview bên dưới vẫn lấy từ dữ liệu phân tích.")}
                        onLoadedData={() => setMediaIssue("")}
                      />
                      {mediaIssue && detail.media.raw_video_url ? (
                        <a className="secondary-link" href={mediaUrl(detail.media.raw_video_url)} target="_blank" rel="noreferrer">
                          Mở video gốc dự phòng
                        </a>
                      ) : null}
                      {(mediaIssue || playbackUnverified) && previewImage ? (
                        <img className="video-fallback-frame" src={mediaUrl(previewImage)} alt="Video preview frame" loading="lazy" decoding="async" />
                      ) : null}
                    </>
                  ) : previewImage ? (
                    <div className="empty-state">Dang hien thi frame preview thay cho video local.</div>
                  ) : (
                    <div className="empty-state">Chưa tìm thấy file video local để phát.</div>
                  )}
                  {(playbackBlocked || playbackUnverified || !detail.media.video_url) && previewImage ? (
                    <img className="video-fallback-frame" src={mediaUrl(previewImage)} alt="Video preview frame" loading="lazy" decoding="async" />
                  ) : null}
                  <ArtifactExportPanel token={token} identifier={String(selectedVideo._detail_id ?? selectedId)} detail={detail} onSaved={reloadDetail} />
                </section>
              ) : null}
              {resultSubtab === "charts" ? (
                <AnalysisCharts
                  chart={detail.chart}
                  onSendCharts={
                    payload.user.role_key === "researcher" || payload.user.role_key === "admin"
                      ? async (phaseLabel, metrics) => {
                          const summary = [
                            `NCV đã lưu và gửi biểu đồ phân tích (${phaseLabel}).`,
                            `Accuracy: ${asText(metrics.accuracy ?? "--")}%`,
                            `PASS/NEAR/FAIL/UNKNOWN: ${asText(metrics.pass_frames ?? 0)}/${asText(metrics.near_frames ?? 0)}/${asText(metrics.fail_frames ?? 0)}/${asText(metrics.unknown_frames ?? 0)}`,
                            `MAE: ${asText(metrics.mae ?? "--")}°; ICC: ${asText(metrics.icc ?? "--")}`,
                          ].join("\n");
                          await api.createEvaluation(token, String(selectedVideo._detail_id ?? selectedId), {
                            doctor_result: "Gần đúng",
                            errors: [],
                            comments: summary,
                            plan: "Đã gửi biểu đồ phân tích từ NCV.",
                            comments_ncv: `Đã gửi biểu đồ ${phaseLabel} cho bệnh nhân và Bác sĩ/KTV.`,
                          });
                          reloadDetail();
                      }
                      : undefined
                  }
                  onSaveChartImage={
                    payload.user.role_key === "researcher" || payload.user.role_key === "admin"
                      ? async ({ phase, chartName, filename, imageData, metrics }) => {
                          await api.saveChartExport(token, String(selectedVideo._detail_id ?? selectedId), {
                            phase,
                            chart_name: chartName,
                            filename,
                            image_data: imageData,
                            metrics,
                          });
                        }
                      : undefined
                  }
                />
              ) : null}
              <section className="result-card evaluation-scroll-card">
                <h3>Nhận xét đã gửi cho bệnh nhân</h3>
                {latest ? (
                  <div className="evaluation-timeline">
                    {detail.evaluations.map((evaluation, index) => (
                      <article key={`${evaluation.time || index}-${evaluation.doctor_username || index}`}>
                        <div>
                          <b>{asText(evaluation.doctor_name || evaluation.doctor_username)} · {asText(evaluation.doctor_result)}</b>
                          <span>{asText(evaluation.time)}</span>
                        </div>
                        <p>{asText(evaluation.comments)}</p>
                        {evaluation.comments_ncv ? <p><b>Ghi chú NCV:</b> {asText(evaluation.comments_ncv)}</p> : null}
                        <p>{asText(evaluation.plan)}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">Chưa có nhận xét bác sĩ/NCV.</div>
                )}
              </section>
              {resultSubtab === "media" ? (
                <FrameGallery
                  token={token}
                  identifier={String(selectedVideo._detail_id ?? selectedId)}
                  detail={detail}
                  frameStart={frameStart}
                  frameEnd={frameEnd}
                  frameTotal={frameTotal}
                  framePage={framePage}
                  framePages={framePages}
                  canPrevFrames={canPrevFrames}
                  canNextFrames={canNextFrames}
                  moveFramePage={moveFramePage}
                  goFramePage={goFramePage}
                  zoomFrame={zoomFrame}
                  setZoomFrame={setZoomFrame}
                  phase={framePhase}
                  status={frameStatus}
                  setPhase={(value) => {
                    setFrameOffset(0);
                    setFramePhase(value);
                  }}
                  setStatus={(value) => {
                    setFrameOffset(0);
                    setFrameStatus(value);
                  }}
                  onSaved={reloadDetail}
                />
              ) : null}
            </>
          ) : null}
        </section>
      </div>
    </section>
  );
}

function statusClass(status: unknown) {
  const text = asText(status).toLowerCase();
  const plain = foldedText(status);
  if (plain.includes("near") || plain.includes("gan")) return "near";
  if (plain.includes("unknown") || plain.includes("no pose") || plain.includes("khong")) return "unknown";
  if (plain.includes("pass") || plain.includes("dung")) return "pass";
  if (text.includes("pass") || text.includes("đúng") || text.includes("dung")) return "pass";
  if (text.includes("near") || text.includes("gần") || text.includes("gan")) return "near";
  if (text.includes("fail") || text.includes("sai")) return "fail";
  return "neutral";
}

function confidenceText(value: unknown) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "";
  return `${num > 1 ? num.toFixed(0) : (num * 100).toFixed(0)}%`;
}

function mlDisplayLabel(frame: VideoDetailPayload["frames"][number]) {
  if (isUnknownFrame(frame)) return "UNKNOWN";
  const label = asText(frame.ml_label);
  const plain = foldedText(label);
  if (plain === "1" || plain.includes("gan") || plain.includes("near")) return "Gan dung";
  if (plain === "2" || plain.includes("dung") || plain.includes("pass")) return "Dung";
  if (plain === "0" || plain.includes("sai") || plain.includes("fail")) return "Sai";
  return label || "N/A";
}

function exerciseKeyFromText(value: unknown) {
  const text = asText(value).toLowerCase();
  if (text.includes("codman") || text.includes("con l")) return "codman";
  if (text.includes("pulley") || text.includes("gậy") || text.includes("gay")) return "pulley";
  return "";
}

function detailExerciseKey(detail?: VideoDetailPayload | null) {
  if (!detail) return "";
  const firstFrameKey = asText(detail.frames?.find((frame) => frame.exercise_key)?.exercise_key).toLowerCase();
  if (firstFrameKey) return firstFrameKey;
  const video = detail.video || {};
  return exerciseKeyFromText(video.exercise || video.exercise_key || video.video_name);
}

function isUnknownFrame(frame: VideoDetailPayload["frames"][number]) {
  const status = `${asText(frame.phase_status)} ${asText(frame.status)} ${asText(frame.ml_label)}`.toLowerCase();
  return Boolean(frame.filtered_stranger) || status.includes("unknown") || status.includes("khong") || status.includes("không") || status.includes("no pose");
}

function FrameMetrics({ frame }: { frame: VideoDetailPayload["frames"][number] }) {
  const confidence = confidenceText(frame.ml_confidence);
  const label = mlDisplayLabel(frame);
  const passProb = confidenceText(frame.ml_prob_pass);
  const failProb = confidenceText(frame.ml_prob_fail);
  const nearProb = confidenceText(frame.ml_prob_near);
  const hasSideAngles = frame.left_shoulder != null || frame.right_shoulder != null || frame.left_elbow != null || frame.right_elbow != null;
  const isCodman = String(frame.exercise_key || "").toLowerCase() === "codman";
  const posePoints = Number(frame.pose_points ?? 0);
  const poseText = Number.isFinite(posePoints) && posePoints > 0 ? `${posePoints}/33` : "N/A";
  const isFilteredStranger = isUnknownFrame(frame);
  if (isFilteredStranger) {
    const reason = asText(frame.stranger_reason).includes("helper") || asText(frame.stranger_reason).includes("people")
      ? "Lẫn người khác / người hỗ trợ"
      : "Thiếu pose hoặc không nhận dạng đủ 33 điểm";
    return (
      <div className="frame-metrics frame-metrics-unknown">
        <div className="metric-row metric-row-wrap">
          <span>Trạng thái</span>
          <b>UNKNOWN - KHÔNG NHẬN DẠNG</b>
        </div>
        <div className="metric-row metric-row-wrap">
          <span>Lý do</span>
          <b>{reason}</b>
        </div>
        <div className="metric-row metric-row-wrap">
          <span>Góc / REF / ML</span>
          <b>UNKNOWN - không chấm điểm frame này</b>
        </div>
      </div>
    );
  }
  return (
    <div className="frame-metrics">
      {isCodman ? (
        <>
          <div className="metric-row metric-row-wrap">
            <span>Phải: Vai {fmtNumber(frame.right_shoulder ?? frame.angle)} deg / {fmtNumber(frame.right_shoulder_ref ?? frame.shoulder_ref)} deg</span>
            <b>Khuỷu {fmtNumber(frame.right_elbow ?? frame.elbow)} deg / {fmtNumber(frame.right_elbow_ref ?? frame.elbow_ref)} deg</b>
          </div>
          <div className="metric-row metric-row-wrap">
            <span>{frame.phase_label || "Giai đoạn"} - REF +/-{asText(frame.threshold)} deg</span>
            <b>Delta vai {fmtNumber(frame.shoulder_delta)} deg - khuỷu {fmtNumber(frame.elbow_delta)} deg</b>
          </div>
        </>
      ) : hasSideAngles ? (
        <>
          <div className="metric-row metric-row-wrap">
            <span>Trái: Vai {fmtNumber(frame.left_shoulder)} deg / {fmtNumber(frame.left_shoulder_ref ?? frame.shoulder_ref)} deg</span>
            <b>Khuỷu {fmtNumber(frame.left_elbow)} deg / {fmtNumber(frame.left_elbow_ref ?? frame.elbow_ref)} deg</b>
          </div>
          <div className="metric-row metric-row-wrap">
            <span>Phải: Vai {fmtNumber(frame.right_shoulder)} deg / {fmtNumber(frame.right_shoulder_ref ?? frame.shoulder_ref)} deg</span>
            <b>Khuỷu {fmtNumber(frame.right_elbow)} deg / {fmtNumber(frame.right_elbow_ref ?? frame.elbow_ref)} deg</b>
          </div>
        </>
      ) : (
        <>
          <div className="metric-row">
            <span>Vai: {fmtNumber(frame.angle)} deg / {fmtNumber(frame.shoulder_ref)} deg</span>
            <b>Delta {fmtNumber(frame.shoulder_delta)} deg</b>
          </div>
          <div className="metric-row">
            <span>Khuỷu: {fmtNumber(frame.elbow)} deg / {fmtNumber(frame.elbow_ref)} deg</span>
            <b>Delta {fmtNumber(frame.elbow_delta)} deg</b>
          </div>
        </>
      )}
      <div className="metric-row">
        <span>Pose</span>
        <b>{poseText}{frame.pose_complete ? " OK" : ""}</b>
      </div>
      <div className="metric-row">
        <span>Model</span>
        <b>ML - {label}{confidence ? ` - tin cay ${confidence}` : ""}</b>
      </div>
      {frame.ref_source ? (
        <div className="metric-row metric-row-wrap">
          <span>REF YouTube</span>
          <b>{asText(frame.youtube_ref_exercise_id || frame.motion_type || frame.ref_source)}{frame.youtube_ref_time ? ` · ${fmtNumber(frame.youtube_ref_time)}s` : ""}</b>
        </div>
      ) : null}
      <div className="metric-row">
        <span>ML:</span>
        <b>{label}{confidence ? ` ${confidence}` : ""}</b>
      </div>
      {(passProb || failProb || nearProb) ? (
        <div className="metric-row metric-row-wrap">
          <span>Xác suất 3 lớp:</span>
          <b>Đúng {passProb || "N/A"} - Sai {failProb || "N/A"} - Gần đúng {nearProb || "N/A"}</b>
        </div>
      ) : null}
    </div>
  );
}

type FrameGroup = NonNullable<VideoDetailPayload["frame_groups"]>[number];

function PhaseVideoPlayer({
  detail,
  mediaKey,
  src,
  poster,
  portrait = false,
  displayRotation = 0,
  onPhaseChange,
  onError,
  onLoadedData,
}: {
  detail: VideoDetailPayload;
  mediaKey?: string;
  src: string;
  poster?: string;
  portrait?: boolean;
  displayRotation?: number;
  onPhaseChange?: (phase: string) => void;
  onError?: () => void;
  onLoadedData?: () => void;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [duration, setDuration] = useState(0);
  const [activePhase, setActivePhase] = useState("all");
  const [playWindow, setPlayWindow] = useState<{ key: string; end: number } | null>(null);
  const playbackMemoryKey = `rehab-video-playback:${mediaKey || src}`;
  const groups = (detail.frame_groups || []).filter((group) => ["all", "g1", "g2", "g3", "overview"].includes(group.key));
  const hasCodmanPhases = groups.some((group) => group.key === "g1");
  const phaseGroups = hasCodmanPhases
    ? groups.filter((group) => ["all", "g1", "g2", "g3"].includes(group.key))
    : groups.filter((group) => ["all", "overview"].includes(group.key));

  const rememberPlayback = (video: HTMLVideoElement) => {
    if (!Number.isFinite(video.currentTime)) return;
    try {
      window.sessionStorage.setItem(
        playbackMemoryKey,
        JSON.stringify({ time: video.currentTime, wasPlaying: !video.paused && !video.ended, updatedAt: Date.now() }),
      );
    } catch {
      // Best-effort only; playback must keep working when storage is unavailable.
    }
  };

  const restorePlayback = (video: HTMLVideoElement) => {
    try {
      const raw = window.sessionStorage.getItem(playbackMemoryKey);
      if (!raw) return;
      const saved = JSON.parse(raw) as { time?: number; wasPlaying?: boolean; updatedAt?: number };
      if (!saved.updatedAt || Date.now() - saved.updatedAt > 30 * 60 * 1000) return;
      const savedTime = Number(saved.time || 0);
      if (!Number.isFinite(savedTime) || savedTime < 0.25) return;
      const safeDuration = Number.isFinite(video.duration) && video.duration > 0 ? video.duration : savedTime + 1;
      video.currentTime = Math.min(savedTime, Math.max(0, safeDuration - 0.25));
      if (saved.wasPlaying) void video.play().catch(() => undefined);
    } catch {
      // Ignore malformed/stale storage.
    }
  };

  const jumpToPhase = (group: FrameGroup) => {
    const video = videoRef.current;
    setActivePhase(group.key);
    onPhaseChange?.(group.key);
    if (!video || !duration || !detail.frame_total) {
      return;
    }
    if (group.key === "all") {
      setPlayWindow(null);
      video.currentTime = 0;
      rememberPlayback(video);
      return;
    }
    const startRatio = Math.max(0, Math.min(1, (group.start_offset || 0) / detail.frame_total));
    const endRatio = Math.max(startRatio, Math.min(1, (group.end_offset || detail.frame_total) / detail.frame_total));
    const startSecond = duration * startRatio;
    const endSecond = Math.max(startSecond + 0.5, duration * endRatio);
    video.currentTime = startSecond;
    rememberPlayback(video);
    setPlayWindow({ key: group.key, end: endSecond });
    void video.play().catch(() => undefined);
  };

  return (
    <div className={`phase-video-player${portrait ? " portrait-video-player" : ""}${displayRotation === 180 ? " rotate-180-video-player" : ""}`}>
      {phaseGroups.length > 2 ? (
        <div className="video-phase-controls" aria-label="Chọn đoạn video theo giai đoạn Codman">
          {phaseGroups.map((group) => (
            <button key={group.key} type="button" className={activePhase === group.key ? "active" : ""} onClick={() => jumpToPhase(group)}>
              <b>{group.label}</b>
              {group.threshold ? <span>REF ±{group.threshold}°</span> : <span>{group.total} frame</span>}
            </button>
          ))}
        </div>
      ) : null}
      <video
        ref={videoRef}
        controls
        playsInline
        preload="auto"
        poster={poster}
        src={src}
        onLoadedMetadata={(event) => {
          setDuration(event.currentTarget.duration || 0);
          restorePlayback(event.currentTarget);
        }}
        onTimeUpdate={(event) => {
          rememberPlayback(event.currentTarget);
          if (playWindow && event.currentTarget.currentTime >= playWindow.end) {
            event.currentTarget.pause();
            setPlayWindow(null);
          }
        }}
        onPlay={(event) => rememberPlayback(event.currentTarget)}
        onPause={(event) => rememberPlayback(event.currentTarget)}
        onSeeking={(event) => rememberPlayback(event.currentTarget)}
        onEnded={(event) => rememberPlayback(event.currentTarget)}
        onError={onError}
        onLoadedData={onLoadedData}
      />
    </div>
  );
}

function FrameGallery({
  token,
  identifier,
  detail,
  frameStart,
  frameEnd,
  frameTotal,
  framePage,
  framePages,
  canPrevFrames,
  canNextFrames,
  moveFramePage,
  goFramePage,
  zoomFrame,
  setZoomFrame,
  phase,
  setPhase,
  status,
  setStatus,
  onSaved,
  showExportPanel = true,
}: {
  token: string;
  identifier: string | number;
  detail: VideoDetailPayload;
  frameStart: number;
  frameEnd: number;
  frameTotal: number;
  framePage: number;
  framePages: number;
  canPrevFrames: boolean;
  canNextFrames: boolean;
  moveFramePage: (direction: -1 | 1) => void;
  goFramePage: (page: number) => void;
  zoomFrame: VideoDetailPayload["frames"][number] | null;
  setZoomFrame: (frame: VideoDetailPayload["frames"][number] | null) => void;
  phase: string;
  setPhase: (value: string) => void;
  status: string;
  setStatus: (value: string) => void;
  onSaved: () => void;
  showExportPanel?: boolean;
}) {
  const groups = detail.frame_groups?.length ? detail.frame_groups : [{ key: "all", label: "Tất cả", total: frameTotal, pass: 0, near: 0, fail: 0, unknown: 0 }];
  const statusFilters = ["ALL", "PASS", "NEAR", "FAIL", "UNKNOWN", "ML"];
  const visibleFrames = detail.frames;

  return (
    <section className="result-card frame-result-card">
      <div className="frame-gallery-head">
        <div>
          <h3>Frame Gallery</h3>
          <p className="artifact-note">
            {detail.media.frame_data_exists ? "Frame khung xương/trích xuất AI, chia theo giai đoạn như app.py." : "Preview từ video gốc vì chưa có artifact khung xương AI đầy đủ."}
          </p>
        </div>
        <span className="role-pill researcher">
          {frameTotal ? `${frameStart + 1}-${frameEnd}/${frameTotal}` : "0/0"} frame theo bộ lọc
        </span>
      </div>
      {showExportPanel ? <ArtifactExportPanel token={token} identifier={identifier} detail={detail} onSaved={onSaved} compact /> : null}

      <div className="phase-filter-grid">
        {groups.map((group) => (
          <button
            key={group.key}
            className={phase === group.key ? "active" : ""}
            type="button"
            onClick={() => setPhase(group.key)}
          >
            <b>{group.label}</b>
            <span>{group.total} frame{group.threshold ? ` · ±${group.threshold}°` : ""}</span>
            <small>PASS {group.pass} · NEAR {group.near} · FAIL {group.fail} · UNKNOWN {group.unknown || 0}</small>
          </button>
        ))}
      </div>

      <div className="status-filter-row">
        {statusFilters.map((item) => (
          <button key={item} className={status === item ? "active" : ""} type="button" onClick={() => setStatus(item)}>
            {item === "ALL" ? "Tất cả" : item === "ML" ? "Có ML" : item === "UNKNOWN" ? "UNKNOWN" : item}
          </button>
        ))}
      </div>

      <details className="frame-legend">
        <summary>Giải thích REF/ML</summary>
        <p>
          REF so góc vai và khuỷu với video YouTube mẫu: bài gậy/Pulley chấm cả vai và khuỷu hai bên với REF ±30°; Codman chỉ chấm vai và khuỷu tay phải, chia G1 ±45°, G2 ±30°, G3 ±15°.
        </p>
        <p>ML là nhãn từ pose classifier nếu artifact đã có thông tin mô hình và độ tin cậy.</p>
      </details>

      <div className="frame-pager-row">
        <span>
          Đang xem frame {frameTotal ? frameStart + 1 : 0}-{frameEnd} / {frameTotal} · Trang {framePage}/{framePages || 1}
        </span>
        <div>
          <button type="button" onClick={() => moveFramePage(-1)} disabled={!canPrevFrames}>Trước</button>
          <input aria-label="Số trang frame" min={1} max={Math.max(1, framePages)} type="number" value={framePage || 1} onChange={(event) => goFramePage(Number(event.target.value || 1))} />
          <button type="button" onClick={() => moveFramePage(1)} disabled={!canNextFrames}>Sau</button>
        </div>
      </div>

      {visibleFrames.length ? (
        <div className="frame-grid enhanced">
          {visibleFrames.map((frame) => (
            <article key={`${frame.index}-${frame.image_url}-${frame.phase}`}>
              <div className="frame-card-head">
                <b>Frame #{frame.index}</b>
                <span className={`frame-badge ${statusClass(frame.phase_status || frame.status)}`}>{frame.phase_status || frame.status || "N/A"}</span>
              </div>
              {frame.image_url ? (
                <button className="frame-zoom-btn" type="button" onClick={() => setZoomFrame(frame)}>
                  <img src={mediaUrl(frame.image_url)} alt={`Frame ${frame.index}`} loading="lazy" decoding="async" />
                  {frame.source === "video_pose_preview" ? <span className="frame-source-chip">Video + skeleton</span> : null}
                  {frame.source === "video_processed" ? <span className="frame-source-chip">Video khung xương</span> : null}
                  {frame.source === "video_preview" ? <span className="frame-source-chip muted">Video preview</span> : null}
                </button>
              ) : (
                <div className="frame-placeholder">
                  <span>Chưa dựng được ảnh frame này</span>
                </div>
              )}
              <FrameMetrics frame={frame} />
              <div className="frame-meta-grid legacy-frame-meta">
                <span><b>{frame.phase_label || "Tổng quan"}</b> · REF ±{asText(frame.threshold)}°</span>
                <span>Vai {fmtNumber(frame.angle)}° / REF {fmtNumber(frame.shoulder_ref)}° · Δ {fmtNumber(frame.shoulder_delta)}°</span>
                <span>Khuỷu {fmtNumber(frame.elbow)}° / REF {fmtNumber(frame.elbow_ref)}° · Δ {fmtNumber(frame.elbow_delta)}°</span>
                {frame.ml_label ? <span>ML · {frame.ml_label} {confidenceText(frame.ml_confidence) ? `· ${confidenceText(frame.ml_confidence)}` : ""}</span> : null}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">Không có frame khớp bộ lọc hiện tại trên trang này.</div>
      )}

      {zoomFrame && typeof document !== "undefined" ? createPortal(
        <div className="frame-modal" role="dialog" aria-modal="true" onClick={() => setZoomFrame(null)}>
          <div className="frame-modal-inner" onClick={(event) => event.stopPropagation()}>
            <div className="frame-modal-head">
              <strong>Frame #{zoomFrame.index} · {zoomFrame.phase_label || "Tổng quan"}</strong>
              <button type="button" onClick={() => setZoomFrame(null)}>Đóng</button>
            </div>
            <img src={mediaUrl(zoomFrame.image_url)} alt={`Frame ${zoomFrame.index}`} loading="eager" decoding="async" />
            <FrameMetrics frame={zoomFrame} />
            <p className="frame-summary-legacy">
              {zoomFrame.phase_status || zoomFrame.status || "N/A"} · Vai {fmtNumber(zoomFrame.angle)}° / REF {fmtNumber(zoomFrame.shoulder_ref)}° · Khuỷu {fmtNumber(zoomFrame.elbow)}° / REF {fmtNumber(zoomFrame.elbow_ref)}°
            </p>
          </div>
        </div>,
        document.body,
      ) : null}
    </section>
  );
}

function AdminAnalysisControls({ payload }: { payload: DashboardPayload }) {
  const latestVideo = payload.latest_evaluated_videos?.[0] || payload.videos?.[0] || {};
  const analyzedCount = payload.latest_evaluated_videos?.length || 0;
  const runLabel = compactText(latestVideo.video_name || latestVideo.stored_filename || "analysis queue", 42);
  const steps = [
    ["Validate / transcode", "done"],
    ["MediaPipe pass 1", analyzedCount ? "done" : "active"],
    ["Overlay / export", analyzedCount ? "done" : "active"],
    ["Artifact / persist", analyzedCount ? "done" : "active"],
  ];
  return (
    <section className="panel admin-analysis-panel">
      <div className="panel-title with-search">
        <div>
          <Settings size={18} aria-hidden="true" />
          <h2>Hàng đợi phân tích AI</h2>
        </div>
        <span className="role-pill admin">{analyzedCount}/8 video mới nhất có kết quả</span>
      </div>
      <div className="admin-control-grid">
        <label>
          Model
          <select defaultValue="heavy">
            <option value="heavy">MediaPipe Heavy</option>
            <option value="full">MediaPipe Full</option>
            <option value="lite">MediaPipe Lite</option>
          </select>
        </label>
        <label>
          Skip step
          <input defaultValue="2" inputMode="numeric" />
        </label>
        <label>
          Resize width
          <input defaultValue="960" inputMode="numeric" />
        </label>
        <label>
          Confidence
          <input defaultValue="0.65" step="0.05" min="0" max="1" type="number" />
        </label>
      </div>
      <div className="admin-action-row">
        <button className="primary-btn" type="button">
          <PlayCircle size={18} aria-hidden="true" />
          Chạy
        </button>
        <button className="ghost-btn" type="button">
          <RefreshCw size={17} aria-hidden="true" />
          Rerun
        </button>
        <button className="ghost-btn" type="button">
          <RefreshCw size={17} aria-hidden="true" />
          Retry
        </button>
        <button className="ghost-btn" type="button">
          <Lock size={17} aria-hidden="true" />
          Hủy
        </button>
        <button className="ghost-btn" type="button">
          <ClipboardList size={17} aria-hidden="true" />
          History
        </button>
      </div>
      <div className="analysis-status-card">
        <div>
          <span>Run hiện tại</span>
          <strong>{runLabel}</strong>
        </div>
        <div className="analysis-steps">
          {steps.map(([label, state]) => (
            <span className={state} key={label}>{label}</span>
          ))}
        </div>
      </div>
      <div className="pose-classifier-card">
        <div className="panel-title">
          <FlaskConical size={18} aria-hidden="true" />
          <h2>Pose classifier ML</h2>
        </div>
        <div className="pose-status-grid">
          <div>
            <span>Model status</span>
            <strong>{payload.metrics.videos_done ? "Sẵn sàng kiểm tra artifact" : "Chưa có video hoàn tất"}</strong>
          </div>
          <div>
            <span>Checksum</span>
            <strong>dry-run guard</strong>
          </div>
          <div>
            <span>Scope</span>
            <strong>{payload.metrics.research_records} phiếu nghiên cứu</strong>
          </div>
        </div>
        <div className="admin-action-row">
          <button className="ghost-btn" type="button">Train dry-run</button>
          <button className="ghost-btn" type="button">Apply dry-run</button>
          <button className="ghost-btn" type="button">Apply classifier</button>
        </div>
      </div>
    </section>
  );
}

function AnalysisJobControls({
  payload,
  token,
  video,
  detail,
  onReload,
}: {
  payload: DashboardPayload;
  token: string;
  video: Record<string, unknown>;
  detail: VideoDetailPayload | null;
  onReload: () => void;
}) {
  const identifier = String(video._detail_id ?? detail?.id ?? video.stored_filename ?? video.video_name ?? "");
  const stepLabels: Record<string, string> = {
    validate_transcode: "Mở video",
    mediapipe_pass: "MediaPipe skeleton",
    ref_compare: "REF đúng/sai/gần đúng",
    ml_classifier: "Train/apply ML",
    artifact_persist: "Lưu video/frames/database",
  };
  const [options, setOptions] = useState<AnalysisJobOptions>({
    model_type: "MediaPipe Heavy",
    skip_step: 0,
    resize_width: 720,
    min_confidence: 0.65,
  });
  const [job, setJob] = useState<AnalysisJob | null>(detail?.latest_job || null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState<AnalysisJob[]>([]);
  const [lastPollAt, setLastPollAt] = useState<number | null>(null);
  const activeJobRef = useRef(false);
  const onReloadRef = useRef(onReload);

  useEffect(() => {
    onReloadRef.current = onReload;
  }, [onReload]);

  useEffect(() => {
    setJob(detail?.latest_job || null);
    setMessage("");
    setHistoryOpen(false);
    setHistory([]);
  }, [detail?.id, detail?.latest_job?.run_id]);

  useEffect(() => {
    if (!identifier) return undefined;
    let cancelled = false;
    let inFlight = false;
    const poll = async () => {
      if (inFlight) return;
      inFlight = true;
      try {
        const payloadJob = await api.latestAnalysisJob(token, identifier);
        if (cancelled) return;
        const nextJob = payloadJob.job;
        const nextActive = isActiveJobStatus(nextJob?.status);
        if (activeJobRef.current && !nextActive) {
          window.setTimeout(() => onReloadRef.current(), 400);
        }
        activeJobRef.current = nextActive;
        setJob(nextJob);
        setLastPollAt(Date.now());
      } catch {
        if (!cancelled) {
          setMessage("Không tải được tiến độ job phân tích, đang tự thử lại...");
        }
      } finally {
        inFlight = false;
      }
    };
    poll();
    const timer = window.setInterval(poll, 1000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [identifier, token]);

  function updateOption(key: keyof AnalysisJobOptions, value: string) {
    setOptions((current) => ({
      ...current,
      [key]: key === "model_type" ? value : Number(value),
    }));
  }

  async function runAction(action: "start" | "rerun" | "retry" | "cancel" | "history" | "refresh") {
    if (!identifier) {
      setMessage("Chưa chọn được video để phân tích.");
      return;
    }
    setBusy(action);
    setMessage("");
    try {
      if (action === "start") {
        const result = await api.startAnalysisJob(token, identifier, options);
        setJob(result.job);
        setMessage("Đã tạo job phân tích mới.");
      } else if (action === "rerun") {
        const result = await api.rerunAnalysisJob(token, identifier, options);
        setJob(result.job);
        setMessage("Đã chạy lại phân tích cho video đang chọn.");
      } else if (action === "retry") {
        const result = await api.retryAnalysisJob(token, identifier);
        setJob(result.job);
        setMessage("Đã retry job phân tích.");
      } else if (action === "cancel") {
        const result = await api.cancelAnalysisJob(token, identifier);
        setJob(result.job);
        setMessage(result.ok ? "Đã hủy job phân tích." : "Video này chưa có job để hủy.");
      } else if (action === "history") {
        const result = await api.analysisJobHistory(token, identifier);
        setHistory(result.items || []);
        setHistoryOpen((open) => !open);
      } else {
        const result = await api.latestAnalysisJob(token, identifier);
        setJob(result.job);
        setMessage("Đã làm mới trạng thái job.");
      }
      if (action === "refresh" || action === "cancel" || action === "history") {
        window.setTimeout(onReload, action === "refresh" ? 0 : 500);
      }
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thao tác được job phân tích.");
    } finally {
      setBusy("");
    }
  }

  const steps = (job?.steps?.length
    ? job.steps
      : [
        { key: "validate_transcode", label: "Mở video", status: "pending" },
        { key: "mediapipe_pass", label: "MediaPipe skeleton", status: "pending" },
        { key: "ref_compare", label: "REF đúng/sai/gần đúng", status: "pending" },
        { key: "ml_classifier", label: "Train/apply ML", status: "pending" },
        { key: "artifact_persist", label: "Lưu video/frames/database", status: "pending" },
      ]).map((step) => ({ ...step, label: stepLabels[String(step.key)] || step.label }));
  const statusText = job?.status || "idle";
  const progressValue = Math.max(0, Math.min(1, Number(job?.progress || 0)));
  const progressPercent = progressValue * 100;
  const progressPct = Math.round(progressPercent);
  const frameMatch = String(job?.status_msg || "").match(/frame\s+(\d+)\s*\/\s*(\d+)/i);
  const currentFrame = Number(job?.current_frame || 0) || (frameMatch ? Number(frameMatch[1]) : null);
  const totalFrames = Number(job?.total_frames || 0) || (frameMatch ? Number(frameMatch[2]) : null);
  const framePercent = currentFrame && totalFrames ? Math.min(100, (currentFrame / totalFrames) * 100) : 0;
  const fpsText = Number(job?.fps_effective || 0) > 0 ? `${Number(job?.fps_effective).toFixed(2)} fps` : "";
  const pollText = lastPollAt ? `cập nhật ${new Date(lastPollAt).toLocaleTimeString("vi-VN")}` : "";
  const activeStep = steps.find((step) => step.status === "active") || steps.find((step) => step.status === "pending") || steps[steps.length - 1];
  const canRun = Boolean(identifier && payload.user.role_key !== "patient");
  const isRunning = Boolean(busy) || ["queued", "processing", "ready_for_ai_worker"].includes(statusText);
  const progressLabel = isRunning && progressPercent > 0 && progressPercent < 99.5 ? `${progressPercent.toFixed(1)}%` : `${progressPct}%`;
  const jobMessage =
    job?.status_msg ||
    (detail?.media.analysis_artifact_exists
      ? "Có thể chạy lại để cập nhật REF/ML/video/frames cho video đang chọn."
      : "Video này đang thiếu REF/ML hoặc artifact; bấm chạy phân tích mới để tạo dữ liệu.");

  return (
    <section className="panel admin-analysis-panel selected-analysis-panel">
      <div className={`analysis-progress-hero ${isRunning ? "running" : ""}`}>
        <div>
          <b>{isRunning ? "Đang chạy phân tích cho video đang chọn" : "Sẵn sàng chạy lại phân tích"}</b>
          <span>{jobMessage}</span>
        </div>
        <strong>{progressLabel}</strong>
        <div className="analysis-progress-track" aria-hidden="true">
          <i style={{ width: `${Math.max(isRunning ? 8 : 2, Math.min(100, progressPercent))}%` }} />
        </div>
        <small>
          {busy ? "Đang gửi yêu cầu..." : activeStep?.label || "Chờ thao tác"}
          {statusText === "ready_for_ai_worker" ? " · Backend đã nhận job, chờ runner MediaPipe thật." : ""}
        </small>
        {currentFrame && totalFrames ? (
          <div className="analysis-frame-live">
            <span className="live-dot" aria-hidden="true" />
            <b>Frame đang trích xuất</b>
            <strong>
              {currentFrame.toLocaleString("vi-VN")} / {totalFrames.toLocaleString("vi-VN")}
            </strong>
            <small>{[fpsText, pollText].filter(Boolean).join(" · ")}</small>
            <i aria-hidden="true">
              <em style={{ width: `${Math.max(1, framePercent)}%` }} />
            </i>
          </div>
        ) : null}
      </div>
      <div className="panel-title with-search">
        <div>
          <Settings size={18} aria-hidden="true" />
          <h2>Chạy lại phân tích AI</h2>
        </div>
        <span className={`role-pill ${statusText === "success" ? "researcher" : "admin"}`}>
          {statusText} · {progressLabel}
        </span>
      </div>
      <div className="admin-control-grid">
        <label>
          Model
          <select value={options.model_type} onChange={(event) => updateOption("model_type", event.target.value)}>
            <option value="MediaPipe Heavy">MediaPipe Heavy</option>
            <option value="MediaPipe Full">MediaPipe Full</option>
            <option value="MediaPipe Lite">MediaPipe Lite</option>
          </select>
        </label>
        <label>
          Skip step
          <input value={options.skip_step} min="0" max="30" inputMode="numeric" onChange={(event) => updateOption("skip_step", event.target.value)} />
        </label>
        <label>
          Resize width
          <input value={options.resize_width} min="240" max="2160" inputMode="numeric" onChange={(event) => updateOption("resize_width", event.target.value)} />
        </label>
        <label>
          Confidence
          <input value={options.min_confidence} step="0.05" min="0" max="1" type="number" onChange={(event) => updateOption("min_confidence", event.target.value)} />
        </label>
      </div>
      <div className="admin-action-row">
        <button className="primary-btn" disabled={!canRun || Boolean(busy) || isRunning} onClick={() => runAction("start")} type="button">
          <PlayCircle size={18} aria-hidden="true" />
          Chạy mới
        </button>
        <button className="ghost-btn" disabled={!canRun || Boolean(busy) || isRunning} onClick={() => runAction("rerun")} type="button">
          <RefreshCw size={17} aria-hidden="true" />
          Chạy lại
        </button>
        <button className="ghost-btn" disabled={!canRun || Boolean(busy) || isRunning} onClick={() => runAction("retry")} type="button">
          <RefreshCw size={17} aria-hidden="true" />
          Retry
        </button>
        <button className="ghost-btn" disabled={!canRun || busy === "cancel"} onClick={() => runAction("cancel")} type="button">
          <Lock size={17} aria-hidden="true" />
          Hủy
        </button>
        <button className="ghost-btn" disabled={!identifier || Boolean(busy)} onClick={() => runAction("history")} type="button">
          <ClipboardList size={17} aria-hidden="true" />
          History
        </button>
        <button className="ghost-btn" disabled={!identifier || Boolean(busy)} onClick={() => runAction("refresh")} type="button">
          <Search size={17} aria-hidden="true" />
          Cập nhật
        </button>
      </div>
      {message ? <div className={`alert ${message.includes("Không") || message.includes("Chưa") ? "error" : "success"}`}>{message}</div> : null}
      <div className="analysis-status-card">
        <div>
          <span>Video đang chọn</span>
          <strong>{compactText(video.video_name || video.stored_filename || detail?.video.video_name || "Chưa chọn video", 84)}</strong>
          <small>{job?.status_msg || "Job sẽ ghi tiến độ theo từng bước xử lý."}</small>
        </div>
        <div className="analysis-steps">
          {steps.map((step) => (
            <span className={step.status} key={step.key}>{step.label}</span>
          ))}
        </div>
      </div>
      {historyOpen ? (
        <div className="job-history-list">
          {history.length ? (
            history.slice().reverse().slice(0, 8).map((item) => (
              <div key={item.run_id || item.job_id}>
                <b>{item.status}</b>
                <span>{compactText(item.status_msg || item.error_msg || item.updated_at, 120)}</span>
              </div>
            ))
          ) : (
            <div className="empty-state">Chưa có lịch sử job cho video này.</div>
          )}
        </div>
      ) : null}
      <div className="pose-classifier-card">
        <div className="panel-title">
          <FlaskConical size={18} aria-hidden="true" />
          <h2>Pose classifier ML</h2>
        </div>
        <div className="pose-status-grid">
          <div>
            <span>Model status</span>
            <strong>{payload.metrics.videos_done ? "Sẵn sàng kiểm tra artifact" : "Chưa có video hoàn tất"}</strong>
          </div>
          <div>
            <span>Checksum</span>
            <strong>{job?.run_id ? compactText(job.run_id, 32) : "dry-run guard"}</strong>
          </div>
          <div>
            <span>Scope</span>
            <strong>{payload.metrics.research_records} phiếu nghiên cứu</strong>
          </div>
        </div>
      </div>
    </section>
  );
}

function AdminVideoWorkspace({
  payload,
  token,
}: {
  payload: DashboardPayload;
  token: string;
}) {
  return (
    <section className="workspace-section">
      <VideoResultWorkspace
        payload={payload}
        token={token}
        title="Video và kết quả AI"
        controls={(video, detail, reload) => (
          <AnalysisJobControls payload={payload} token={token} video={video} detail={detail} onReload={reload} />
        )}
      />
    </section>
  );
}

function AdminResearchWorkspace({ payload }: { payload: DashboardPayload }) {
  const aiVideoDoneCount = researcherAiVideoCount(payload);
  const videoScopeCount = payload.metrics.videos || payload.videos.length;
  const syncItems = [
    ["Status", "local JSON workspace"],
    ["Dry-run metadata", `${payload.metrics.research_records} bản ghi NCKH`],
    ["Artifact", `${aiVideoDoneCount} video đã phân tích`],
    ["Report sanitize", "không đồng bộ users.json"],
  ];
  return (
    <section className="workspace-section">
      <div className="panel-title page-line">
        <FlaskConical size={18} aria-hidden="true" />
        <h2>Dữ liệu NCKH / Phiếu nghiên cứu</h2>
      </div>
      <div className="panel-grid">
        <section className="panel hf-sync-panel">
          <div className="panel-title with-search">
            <div>
              <Upload size={18} aria-hidden="true" />
              <h2>Hugging Face sync</h2>
            </div>
            <span className="role-pill researcher">Admin / NCV</span>
          </div>
          <div className="hf-status-grid">
            {syncItems.map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <div className="admin-action-row">
            <button className="ghost-btn" type="button">Dry-run metadata sync</button>
            <button className="ghost-btn" type="button">Upload artifact</button>
            <button className="ghost-btn" type="button">Sanitize report</button>
          </div>
        </section>
        <section className="panel">
          <div className="panel-title">
            <Database size={18} aria-hidden="true" />
            <h2>Tóm tắt dữ liệu</h2>
          </div>
          <div className="result-summary">
            <StatCard icon={Video} label="Video AI xong" value={aiVideoDoneCount} hint={`${videoScopeCount} video trong scope`} />
            <StatCard icon={ClipboardList} label="Phiếu NCKH" value={payload.metrics.research_records} hint={`${payload.metrics.evaluations} đánh giá`} />
            <StatCard icon={Activity} label="Lịch / triệu chứng" value={payload.metrics.schedules + payload.metrics.symptoms} hint="Dữ liệu hỗ trợ theo dõi" />
          </div>
        </section>
      </div>
      <ResearchView payload={payload} />
    </section>
  );
}

function PatientDataView({
  payload,
  token,
  onSaved,
}: {
  payload: DashboardPayload;
  token: string;
  onSaved: () => void;
}) {
  const patientOptions = payload.users.filter((user) => user.role_key === "patient");
  const isDoctor = payload.user.role_key === "doctor_ktv";
  const [scheduleTab, setScheduleTab] = useState<"appointment" | "exercise" | "medication" | "create">("appointment");
  const [scheduleDraft, setScheduleDraft] = useState({
    patient_username: patientOptions[0]?.username || "",
    kind: "exercise",
    title: "Nhắc tập phục hồi chức năng",
    date: new Date().toISOString().slice(0, 10),
    time: "08:00",
    note: "",
  });
  const [scheduleMessage, setScheduleMessage] = useState("");
  const [savingSchedule, setSavingSchedule] = useState(false);

  async function submitSchedule(event: FormEvent) {
    event.preventDefault();
    setSavingSchedule(true);
    setScheduleMessage("");
    try {
      const kindLabel = scheduleDraft.kind === "appointment" ? "Lịch hẹn khám" : scheduleDraft.kind === "medication" ? "Lịch uống thuốc" : "Lịch tập luyện";
      await api.createSchedule(token, { ...scheduleDraft, title: `${kindLabel}: ${scheduleDraft.title}` });
      setScheduleMessage("Đã gửi lịch nhắc cho bệnh nhân.");
      setScheduleDraft({
        patient_username: patientOptions[0]?.username || "",
        kind: "exercise",
        title: "Nhắc tập phục hồi chức năng",
        date: new Date().toISOString().slice(0, 10),
        time: "08:00",
        note: "",
      });
      onSaved();
    } catch (error) {
      setScheduleMessage(error instanceof ApiError ? error.message : "Không thể gửi lịch nhắc.");
    } finally {
      setSavingSchedule(false);
    }
  }
  const kindOfSchedule = (record: Record<string, unknown>) => {
    const kind = asText(record.kind).toLowerCase();
    if (["appointment", "exercise", "medication"].includes(kind)) return kind;
    const text = `${asText(record.title)} ${asText(record.note)}`.toLowerCase();
    if (text.includes("hẹn") || text.includes("khám")) return "appointment";
    if (text.includes("thuốc") || text.includes("uống")) return "medication";
    return "exercise";
  };
  const scheduleRows = payload.schedules.filter((record) => kindOfSchedule(record) === scheduleTab);
  const scheduleTabItems: { key: typeof scheduleTab; label: string; icon: typeof Activity }[] = [
    { key: "appointment", label: "Lịch hẹn khám", icon: Stethoscope },
    { key: "exercise", label: "Lịch tập luyện", icon: Activity },
    { key: "medication", label: "Lịch uống thuốc", icon: ClipboardList },
    ...(isDoctor ? [{ key: "create" as const, label: "Thêm mới", icon: Mail }] : []),
  ];

  return (
    <section className="workspace-section">
      <div className="panel-title page-line">
        <Activity size={18} aria-hidden="true" />
        <h2>Lịch nhắc nhở & hẹn khám</h2>
      </div>
      <details className="panel wide-panel symptom-accordion">
        <summary>
          <span><Activity size={18} aria-hidden="true" /> Khai báo triệu chứng</span>
          <b>{payload.symptoms.length} bản ghi</b>
        </summary>
        <DataTable
          rows={payload.symptoms}
          empty="Chưa có khai báo triệu chứng."
          columns={[
            { key: "full_name", label: "Bệnh nhân" },
            { key: "vas", label: "VAS" },
            { key: "exercise", label: "Bài tập" },
            { key: "symptoms", label: "Triệu chứng", wide: true },
            { key: "time", label: "Thời gian" },
          ]}
        />
      </details>
      <div className="schedule-tabs" role="tablist" aria-label="Lịch nhắc nhở">
        {scheduleTabItems.map(({ key, label, icon: Icon }) => (
          <button key={key} type="button" className={scheduleTab === key ? "active" : ""} onClick={() => setScheduleTab(key)}>
            <Icon size={16} aria-hidden="true" />
            {label}
          </button>
        ))}
      </div>
      {scheduleTab === "create" ? (
        <section className="panel schedule-composer">
          <div className="panel-title">
            <ClipboardList size={18} aria-hidden="true" />
            <h2>Tạo lịch nhắc</h2>
          </div>
          {scheduleMessage ? <div className="alert">{scheduleMessage}</div> : null}
          <div className="schedule-target-note">
            Lịch này sẽ gửi cho: <b>{patientOptions.find((user) => user.username === scheduleDraft.patient_username)?.full_name || scheduleDraft.patient_username || "Chưa chọn bệnh nhân"}</b>
          </div>
          <form className="form-grid compact" onSubmit={submitSchedule}>
            <label>
              Bệnh nhân
              <select value={scheduleDraft.patient_username} onChange={(event) => setScheduleDraft({ ...scheduleDraft, patient_username: event.target.value })}>
                {patientOptions.map((user) => (
                  <option key={user.username} value={user.username}>
                    {user.full_name || user.username}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Loại lịch
              <select value={scheduleDraft.kind} onChange={(event) => setScheduleDraft({ ...scheduleDraft, kind: event.target.value })}>
                <option value="appointment">Lịch hẹn khám</option>
                <option value="exercise">Lịch tập luyện</option>
                <option value="medication">Lịch uống thuốc</option>
              </select>
            </label>
            <label>
              Ngày
              <input type="date" value={scheduleDraft.date} onChange={(event) => setScheduleDraft({ ...scheduleDraft, date: event.target.value })} />
            </label>
            <label>
              Giờ
              <input type="time" value={scheduleDraft.time} onChange={(event) => setScheduleDraft({ ...scheduleDraft, time: event.target.value })} />
            </label>
            <label>
              Nội dung
              <input value={scheduleDraft.title} onChange={(event) => setScheduleDraft({ ...scheduleDraft, title: event.target.value })} />
            </label>
            <label className="span-two">
              Ghi chú
              <textarea value={scheduleDraft.note} onChange={(event) => setScheduleDraft({ ...scheduleDraft, note: event.target.value })} />
            </label>
            <button className="primary-btn" type="submit" disabled={savingSchedule}>
              {savingSchedule ? <RefreshCw size={18} className="spin" aria-hidden="true" /> : <Mail size={18} aria-hidden="true" />}
              Gửi cho bệnh nhân
            </button>
          </form>
        </section>
      ) : (
        <section className="panel wide-panel">
          <div className="panel-title">
            <Activity size={18} aria-hidden="true" />
            <h2>{scheduleTab === "appointment" ? "Lịch hẹn khám" : scheduleTab === "medication" ? "Lịch uống thuốc" : "Lịch tập luyện"}</h2>
          </div>
          <DataTable
            rows={scheduleRows}
            empty="Chưa có lịch nhắc thuộc nhóm này."
            columns={[
              { key: "patient_username", label: "Bệnh nhân" },
              { key: "title", label: "Nội dung", wide: true },
              { key: "date", label: "Ngày" },
              { key: "time", label: "Giờ" },
              { key: "status", label: "Trạng thái" },
            ]}
          />
        </section>
      )}
    </section>
  );
}

function ResearchView({ payload }: { payload: DashboardPayload }) {
  return (
    <section className="workspace-section">
      <div className="panel-title page-line">
        <BarChart3 size={18} aria-hidden="true" />
        <h2>Dữ liệu nghiên cứu</h2>
      </div>
      <DataTable
        rows={payload.research_data}
        empty="Role hiện tại chưa có dữ liệu nghiên cứu để hiển thị."
        columns={[
          { key: "subject_code", label: "Mã mẫu" },
          { key: "patient_username", label: "Bệnh nhân" },
          { key: "diagnosis", label: "Chẩn đoán", wide: true },
          { key: "general_result", label: "Kết quả" },
          { key: "submitted_by", label: "Người nhập" },
          { key: "timestamp", label: "Thời gian" },
        ]}
      />
    </section>
  );
}

function EvaluationFormsView({ payload, token, onSaved }: { payload: DashboardPayload; token: string; onSaved: () => void }) {
  const role = payload.user.role_key;
  const isPatient = role === "patient";
  const isResearchEvaluation = (record: Record<string, unknown>) => {
    const text = [record.doctor_name, record.doctor_username, record.submitted_by, record.source, record.comments_ncv]
      .map((value) => asText(value).toLowerCase())
      .join(" ");
    return text.includes("ncv") || text.includes("nghiên cứu") || text.includes("research") || text.includes("ai_researcher");
  };
  const clinicalRows = payload.evaluations.filter((record) => !isResearchEvaluation(record));
  const researchRows = payload.evaluations.filter((record) => isResearchEvaluation(record));
  const patientRows = payload.evaluations;
  const clinicalColumns = [
    { key: "patient_username", label: "Bệnh nhân" },
    { key: "doctor_name", label: "Bác sĩ/KTV" },
    { key: "doctor_result", label: "Kết quả" },
    { key: "comments", label: "Nhận xét PHCN", wide: true },
    { key: "plan", label: "Kế hoạch", wide: true },
    { key: "time", label: "Thời gian" },
  ];
  const researchColumns = [
    { key: "patient_username", label: "Bệnh nhân" },
    { key: "doctor_name", label: "NCV/AI" },
    { key: "doctor_result", label: "Kết quả" },
    { key: "comments_ncv", label: "Ghi chú NCV", wide: true },
    { key: "comments", label: "Nhận xét", wide: true },
    { key: "time", label: "Thời gian" },
  ];
  if (role === "doctor_ktv") {
    return <DoctorEvaluationWorkspace payload={payload} token={token} onSaved={onSaved} clinicalRows={clinicalRows} researchRows={researchRows} />;
  }
  return (
    <section className="workspace-section">
      <div className="panel-title page-line">
        <ClipboardList size={18} aria-hidden="true" />
        <h2>{isPatient ? "Phiếu đánh giá của tôi" : "Phiếu đánh giá PHCN & NCV"}</h2>
      </div>
      {isPatient ? (
        <section className="panel wide-panel">
          <div className="panel-title with-search">
            <div>
              <FileText size={18} aria-hidden="true" />
              <h2>Kết quả đã gửi cho bệnh nhân</h2>
            </div>
            <span className="role-pill patient">{patientRows.length} phiếu</span>
          </div>
          <DataTable
            rows={patientRows}
            empty="Chưa có phiếu đánh giá nào được gửi cho tài khoản bệnh nhân này."
            columns={[
              { key: "doctor_name", label: "Người đánh giá" },
              { key: "doctor_result", label: "Kết quả" },
              { key: "comments", label: "Nhận xét", wide: true },
              { key: "comments_ncv", label: "Ghi chú NCV", wide: true },
              { key: "plan", label: "Kế hoạch tập", wide: true },
              { key: "time", label: "Thời gian" },
            ]}
          />
        </section>
      ) : (
        <div className="panel-grid evaluation-split-grid">
        <section className="panel wide-panel">
          <div className="panel-title with-search">
            <div>
              <Stethoscope size={18} aria-hidden="true" />
              <h2>Phiếu đánh giá PHCN - Bác sĩ/KTV</h2>
            </div>
            <span className="role-pill doctor">{clinicalRows.length} phiếu</span>
          </div>
          <DataTable
            rows={clinicalRows}
            empty="Chưa có phiếu đánh giá PHCN trong phạm vi tài khoản."
            columns={clinicalColumns}
          />
        </section>
        <section className="panel wide-panel">
          <div className="panel-title with-search">
            <div>
              <Microscope size={18} aria-hidden="true" />
              <h2>Phiếu đánh giá NCV / AI</h2>
            </div>
            <span className="role-pill researcher">{researchRows.length} phiếu</span>
          </div>
          <DataTable
            rows={researchRows}
            empty="Chưa có phiếu NCV/AI trong phạm vi tài khoản."
            columns={researchColumns}
          />
        </section>
        <section className="panel evaluation-form-preview">
          <div className="panel-title">
            <ClipboardList size={18} aria-hidden="true" />
            <h2>Mẫu phiếu PHCN theo app.py</h2>
          </div>
          <div className="evaluation-template-grid">
            <span>1. Thông tin bệnh nhân, chẩn đoán, bài tập và ngày đánh giá.</span>
            <span>2. Lượng giá tầm vận động vai, mức đau VAS, mức an toàn khi tập.</span>
            <span>3. Đối chiếu video: tư thế, biên độ, nhịp tập, lỗi cần chỉnh.</span>
            <span>4. Kết luận: Đúng / Gần đúng / Sai và khuyến nghị tập tiếp.</span>
            <span>5. Kế hoạch: bài tập, số lần, lịch nhắc, tái đánh giá.</span>
          </div>
          <div className="alert">Muốn ghi phiếu thật: Bác sĩ/KTV mở tab Phiếu đánh giá để lưu PHCN hoặc Phiếu NCKH; NCV dùng các nút lưu/gửi video, frames và biểu đồ trong trang kết quả.</div>
        </section>
        <section className="panel evaluation-form-preview">
          <div className="panel-title">
            <Target size={18} aria-hidden="true" />
            <h2>Mẫu phiếu NCV / nghiên cứu</h2>
          </div>
          <div className="evaluation-template-grid">
            <span>1. Kiểm tra artifact, frame gallery, nhãn REF/ML và chỉ số nghiên cứu.</span>
            <span>2. Đối chiếu PASS / NEAR / FAIL theo giai đoạn G1, G2, G3 hoặc tổng quan Pulley.</span>
            <span>3. Ghi chú NCV, trạng thái gửi báo cáo và khả năng dùng cho bộ dữ liệu NCKH.</span>
          </div>
          <div className="alert">Bệnh nhân chỉ thấy phiếu thuộc video/tài khoản của chính họ; các role chuyên môn mới thấy dữ liệu phạm vi rộng hơn.</div>
        </section>
      </div>
      )}
    </section>
  );
}

function ResearchSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="research-section">
      <h3>{title}</h3>
      <div className="research-section-grid">{children}</div>
    </section>
  );
}

const clinicalErrorOptions = ["Vị trí tay chưa đúng", "Biên độ chưa đạt", "Tốc độ quá nhanh/chậm", "Sai tư thế thân người"];

function DoctorEvaluationWorkspace({
  payload,
  token,
  onSaved,
  clinicalRows,
  researchRows,
}: {
  payload: DashboardPayload;
  token: string;
  onSaved: () => void;
  clinicalRows: Record<string, unknown>[];
  researchRows: Record<string, unknown>[];
}) {
  const videos = payload.videos?.length ? payload.videos : payload.latest_evaluated_videos;
  const [subtab, setSubtab] = useState<"clinical" | "research" | "ai" | "media">("clinical");
  const [selected, setSelected] = useState(0);
  const selectedVideo = videos[Math.min(selected, Math.max(0, videos.length - 1))] || {};
  const identifier = String(selectedVideo._detail_id ?? selected);
  const [detail, setDetail] = useState<VideoDetailPayload | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [frameOffset, setFrameOffset] = useState(0);
  const [framePhase, setFramePhase] = useState("all");
  const [frameStatus, setFrameStatus] = useState("ALL");
  const [zoomFrame, setZoomFrame] = useState<VideoDetailPayload["frames"][number] | null>(null);
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    doctor_result: "Đúng",
    errors: [] as string[],
    comments: "",
    plan: "Tiếp tục",
    comments_ncv: "",
  });
  const [researchForm, setResearchForm] = useState({
    interviewer: payload.user.full_name || payload.user.username,
    interview_date: new Date().toISOString().slice(0, 10),
    subject_code: "",
    age: "",
    gender: "Nam (1)",
    area: "Nội thành (1)",
    job: "Nghỉ hưu (7)",
    education: "Trung học phổ thông (4)",
    department: "Khoa PHCN - Y học cổ truyền (1)",
    treatment_type: "Ngoại trú (2)",
    diagnosis: "Viêm quanh khớp vai (P) (ICD-10: M75)",
    shoulder_side: "Vai phải (2)",
    disease_duration: "1 - 3 tháng (2)",
    training_side: "Vai phải",
    pain_level: "Trung bình (4-6)",
    severity: "Trung bình",
    exercise_codman: false,
    exercise_pulley: false,
    exercise_band: false,
    total_reps: "",
    correct_reps: "",
    device: "Điện thoại",
    device_other: "",
    camera_angle: "Chính diện",
    camera_distance: "",
    specialist_comment: "",
    collector_confirmed: true,
  });
  const frameLimit = 16;
  const detailCache = useRef(new Map<string, VideoDetailPayload>());
  const effectiveFrameLimit = subtab === "media" ? frameLimit : 1;
  const includeChart = subtab !== "media";

  useEffect(() => {
    if (!videos.length) {
      setDetail(null);
      return;
    }
    const cacheKey = `${identifier}:${frameOffset}:${effectiveFrameLimit}:${framePhase}:${frameStatus}:${includeChart}`;
    const cached = detailCache.current.get(cacheKey);
    if (cached) {
      setDetail(cached);
      setLoadingDetail(false);
      return;
    }
    setLoadingDetail(true);
    api
      .videoDetail(token, identifier, frameOffset, effectiveFrameLimit, framePhase, frameStatus, includeChart)
      .then((data) => {
        detailCache.current.set(cacheKey, data);
        setDetail(data);
      })
      .catch(() => setDetail(null))
      .finally(() => setLoadingDetail(false));
  }, [identifier, token, videos.length, frameOffset, framePhase, frameStatus, effectiveFrameLimit, includeChart]);

  useEffect(() => {
    setFrameOffset(0);
    setFramePhase("all");
    setFrameStatus("ALL");
    setZoomFrame(null);
  }, [selected]);

  useEffect(() => {
    setFrameOffset(0);
  }, [framePhase, frameStatus]);

  const reloadDetail = () => {
    if (!videos.length) return;
    setLoadingDetail(true);
    api
      .videoDetail(token, identifier, frameOffset, effectiveFrameLimit, framePhase, frameStatus, includeChart)
      .then((data) => {
        detailCache.current.clear();
        detailCache.current.set(`${identifier}:${frameOffset}:${effectiveFrameLimit}:${framePhase}:${frameStatus}:${includeChart}`, data);
        setDetail(data);
      })
      .catch(() => setDetail(null))
      .finally(() => setLoadingDetail(false));
  };
  useEffect(() => {
    return undefined;
  }, [detail?.latest_job?.status, detail?.latest_job?.run_id, identifier, frameOffset, framePhase, frameStatus]);

  async function submitClinical(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await api.createEvaluation(token, identifier, form);
      setMessage("Đã lưu phiếu PHCN và gửi cho bệnh nhân + NCV.");
      setForm({ doctor_result: "Đúng", errors: [], comments: "", plan: "Tiếp tục", comments_ncv: "" });
      onSaved();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể lưu phiếu đánh giá.");
    }
  }

  const toggleClinicalError = (value: string, checked: boolean) => {
    setForm((current) => ({
      ...current,
      errors: checked ? Array.from(new Set([...current.errors, value])) : current.errors.filter((item) => item !== value),
    }));
  };

  async function submitResearch(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const selectedExercises = [
        researchForm.exercise_codman ? "Bài tập con lắc Codman" : "",
        researchForm.exercise_pulley ? "Bài tập với gậy" : "",
        researchForm.exercise_band ? "Bài tập với dây kháng lực" : "",
      ].filter(Boolean);
      const researchSummary = [
        "PHIẾU ĐÁNH GIÁ KỸ THUẬT TẬP LUYỆN",
        `Người phỏng vấn: ${researchForm.interviewer}`,
        `Ngày phỏng vấn: ${researchForm.interview_date}`,
        `Mã đối tượng: ${researchForm.subject_code || asText(selectedVideo.username)}`,
        `Tuổi: ${researchForm.age || "N/A"}; Giới tính: ${researchForm.gender}; Khu vực: ${researchForm.area}`,
        `Nghề nghiệp: ${researchForm.job}; Học vấn: ${researchForm.education}`,
        `Khoa điều trị: ${researchForm.department}; Hình thức: ${researchForm.treatment_type}`,
        `Chẩn đoán: ${researchForm.diagnosis}; Vai tổn thương: ${researchForm.shoulder_side}; Thời gian mắc bệnh: ${researchForm.disease_duration}`,
        `Bên tập luyện: ${researchForm.training_side}; Đau VAS: ${researchForm.pain_level}; Mức độ bệnh: ${researchForm.severity}`,
        `Bài tập ghi hình: ${selectedExercises.join(", ") || asText(selectedVideo.exercise)}`,
        `Tổng số lần: ${researchForm.total_reps || "N/A"}; Đúng kỹ thuật: ${researchForm.correct_reps || "N/A"}`,
        `Thiết bị: ${researchForm.device}${researchForm.device_other ? ` (${researchForm.device_other})` : ""}; Góc quay: ${researchForm.camera_angle}; Khoảng cách: ${researchForm.camera_distance || "N/A"} m`,
        `Nhận xét chuyên môn: ${researchForm.specialist_comment || form.comments || "N/A"}`,
        researchForm.collector_confirmed ? "Người thu thập xác nhận thông tin trung thực." : "Chưa xác nhận người thu thập.",
      ].join("\n");
      await api.createEvaluation(token, identifier, {
        doctor_result: form.doctor_result,
        errors: form.errors,
        comments: researchSummary,
        plan: form.plan || "Theo dõi tiếp và tái đánh giá theo lịch.",
        comments_ncv: form.comments_ncv || "Phiếu NCKH do Bác sĩ/KTV cập nhật.",
      });
      setMessage("Đã lưu phiếu NCKH và gửi cho bệnh nhân + NCV.");
      onSaved();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể lưu phiếu NCKH.");
    }
  }

  const subtabs = [
    ["clinical", "Đánh giá PHCN", ClipboardList],
    ["research", "Phiếu NCKH", FileText],
    ["ai", "Kết quả biểu đồ từ NCV", Microscope],
    ["media", "Video & hình ảnh", Video],
  ] as const;
  const frameStart = detail?.frame_offset || 0;
  const frameTotal = detail?.frame_total || 0;
  const frameEnd = Math.min(frameTotal, frameStart + (detail?.frames.length || 0));
  const framePage = frameTotal ? Math.floor(frameStart / frameLimit) + 1 : 0;
  const framePages = frameTotal ? Math.ceil(frameTotal / frameLimit) : 0;
  const moveFramePage = (direction: -1 | 1) => {
    setFrameOffset((current) => Math.min(Math.max(0, frameTotal - frameLimit), Math.max(0, current + direction * frameLimit)));
  };
  const goFramePage = (page: number) => {
    const safePage = Math.min(Math.max(1, page), Math.max(1, framePages));
    setFrameOffset((safePage - 1) * frameLimit);
  };

  return (
    <section className="workspace-section doctor-evaluation-workspace">
      <div className="panel-title page-line">
        <Stethoscope size={18} aria-hidden="true" />
        <h2>Phiếu đánh giá bác sĩ/KTV</h2>
      </div>
      <div className="doctor-subtabs" role="tablist" aria-label="Phiếu đánh giá bác sĩ">
        {subtabs.map(([key, label, Icon]) => (
          <button key={key} className={subtab === key ? "active" : ""} type="button" onClick={() => setSubtab(key)}>
            <Icon size={16} aria-hidden="true" />
            {label}
          </button>
        ))}
      </div>
      {message ? <div className={`alert ${message.includes("Không") ? "error" : "success"}`}>{message}</div> : null}
      <div className="doctor-eval-layout">
        <section className="panel doctor-video-selector">
          <div className="panel-title">
            <Video size={18} aria-hidden="true" />
            <h2>Chọn video bệnh nhân</h2>
          </div>
          <div className="video-list compact-list">
            {videos.map((video, index) => (
              <button key={`${video._detail_id || index}-${video.video_name || index}`} className={selected === index ? "active" : ""} type="button" onClick={() => setSelected(index)}>
                <b>{compactText(video.video_name, 52)}</b>
                <span>{compactText(video.full_name || video.username, 42)} · {compactText(video.exercise, 42)}</span>
                <small>{asText(video.status)} · AI {asText(video.accuracy)}</small>
              </button>
            ))}
            {!videos.length ? <div className="empty-state">Chưa có video để đánh giá.</div> : null}
          </div>
        </section>
        <section className="panel doctor-eval-main">
          <div className="doctor-selected-head">
            <div>
              <span className="role-pill doctor">Video đang đánh giá</span>
              <h2>{asText(selectedVideo.video_name)}</h2>
              <p>{asText(selectedVideo.full_name || selectedVideo.username)} · {asText(selectedVideo.exercise)}</p>
            </div>
            <span className="role-pill">{loadingDetail ? "Đang tải" : asText(selectedVideo.status)}</span>
          </div>

          {detail && (subtab === "clinical" || subtab === "research") ? (
            <div className="doctor-run-analysis-split">
              <section className="result-card doctor-raw-video-card">
                <h3>Video đã phân tích</h3>
                {detail.media.video_url ? (
                  <PhaseVideoPlayer
                    detail={detail}
                    src={mediaUrl(detail.media.video_url)}
                    poster={detail.frames[0]?.image_url ? mediaUrl(detail.frames[0].image_url) : undefined}
                    portrait={["codman", "pulley"].includes(detailExerciseKey(detail))}
                    displayRotation={Number(detail.media.display_rotation || 0)}
                    onPhaseChange={(value) => {
                      setFrameOffset(0);
                      setFramePhase(value);
                    }}
                  />
                ) : (
                  <div className="empty-state">Chưa tìm thấy video đã phân tích cho bản ghi này.</div>
                )}
              </section>
              <section className="result-card doctor-raw-video-card">
                <h3>Video thô bệnh nhân upload</h3>
                {detail.media.raw_video_url ? (
                  <video
                    controls
                    preload="auto"
                    src={mediaUrl(detail.media.raw_video_url)}
                  />
                ) : (
                  <div className="empty-state">Chưa tìm thấy file video thô bệnh nhân upload cho bản ghi này.</div>
                )}
              </section>
            </div>
          ) : null}

          {subtab === "clinical" ? (
            <form className="doctor-eval-form" onSubmit={submitClinical}>
              <div className="research-form-header">
                <b>PHIẾU ĐÁNH GIÁ KỸ THUẬT ĐỘNG TÁC (GROUND TRUTH)</b>
                <span>Đang đánh giá: {asText(selectedVideo.full_name || selectedVideo.username)} - {asText(selectedVideo.exercise)}</span>
              </div>
              <div className="form-grid compact">
                <label>
                  Kết quả
                  <select value={form.doctor_result} onChange={(event) => setForm({ ...form, doctor_result: event.target.value })}>
                    <option>Đúng</option>
                    <option>Sai</option>
                    <option>Gần đúng</option>
                  </select>
                </label>
                <label className="span-two">
                  Lỗi sai
                  <div className="checkbox-grid">
                    {clinicalErrorOptions.map((option) => (
                      <label className="check-row" key={option}>
                        <input
                          type="checkbox"
                          checked={form.errors.includes(option)}
                          onChange={(event) => toggleClinicalError(option, event.target.checked)}
                        />
                        {option}
                      </label>
                    ))}
                  </div>
                </label>
                <label className="span-two">
                  Nhận xét cho BN
                  <textarea value={form.comments} onChange={(event) => setForm({ ...form, comments: event.target.value })} placeholder="Nhận xét tư thế, biên độ vận động, mức đau, mức an toàn..." />
                </label>
                <label className="span-two">
                  Ghi chú cho NCV
                  <textarea value={form.comments_ncv} onChange={(event) => setForm({ ...form, comments_ncv: event.target.value })} placeholder="Ghi chú nội bộ cho nghiên cứu viên nếu có..." />
                </label>
                <label className="span-two">
                  Chỉ định
                  <select value={form.plan} onChange={(event) => setForm({ ...form, plan: event.target.value })}>
                    <option>Tiếp tục</option>
                    <option>Chuyển bài</option>
                    <option>Khám lại</option>
                  </select>
                </label>
              </div>
              <button className="primary-btn" type="submit" disabled={!videos.length}>
                <Mail size={18} aria-hidden="true" />
                Lưu & gửi phiếu PHCN
              </button>
            </form>
          ) : null}

          {subtab === "research" ? (
            <form className="doctor-eval-form" onSubmit={submitResearch}>
              <div className="research-form-header">
                <b>PHIẾU ĐÁNH GIÁ KỸ THUẬT TẬP LUYỆN</b>
                <span>Bộ công cụ nghiên cứu · gắn với video {asText(selectedVideo.video_name)}</span>
              </div>
              <ResearchSection title="I. Thông tin chung và đặc điểm lâm sàng">
                <label>Người phỏng vấn<input value={researchForm.interviewer} onChange={(event) => setResearchForm({ ...researchForm, interviewer: event.target.value })} /></label>
                <label>Ngày phỏng vấn<input type="date" value={researchForm.interview_date} onChange={(event) => setResearchForm({ ...researchForm, interview_date: event.target.value })} /></label>
                <label>Mã đối tượng<input value={researchForm.subject_code} onChange={(event) => setResearchForm({ ...researchForm, subject_code: event.target.value })} placeholder={asText(selectedVideo.username)} /></label>
                <label>Tuổi<input value={researchForm.age} onChange={(event) => setResearchForm({ ...researchForm, age: event.target.value })} inputMode="numeric" /></label>
                <label>Giới tính<select value={researchForm.gender} onChange={(event) => setResearchForm({ ...researchForm, gender: event.target.value })}><option>Nam (1)</option><option>Nữ (2)</option></select></label>
                <label>Khu vực<select value={researchForm.area} onChange={(event) => setResearchForm({ ...researchForm, area: event.target.value })}><option>Nội thành (1)</option><option>Ngoại thành (2)</option></select></label>
                <label>Nghề nghiệp<select value={researchForm.job} onChange={(event) => setResearchForm({ ...researchForm, job: event.target.value })}><option>Nông dân (1)</option><option>Công nhân (2)</option><option>Cán bộ - viên chức (3)</option><option>Buôn bán (4)</option><option>Nội trợ (5)</option><option>Lao động tự do (6)</option><option>Nghỉ hưu (7)</option><option>Không có nghề nghiệp cụ thể (8)</option></select></label>
                <label>Trình độ học vấn<select value={researchForm.education} onChange={(event) => setResearchForm({ ...researchForm, education: event.target.value })}><option>Mù chữ (1)</option><option>Tiểu học (2)</option><option>Trung học cơ sở (3)</option><option>Trung học phổ thông (4)</option><option>Cao đẳng - đại học (5)</option><option>Không rõ (6)</option></select></label>
                <label>Khoa điều trị<select value={researchForm.department} onChange={(event) => setResearchForm({ ...researchForm, department: event.target.value })}><option>Khoa PHCN - Y học cổ truyền (1)</option><option>Khác (99)</option></select></label>
                <label>Hình thức điều trị<select value={researchForm.treatment_type} onChange={(event) => setResearchForm({ ...researchForm, treatment_type: event.target.value })}><option>Nội trú (1)</option><option>Ngoại trú (2)</option></select></label>
                <label>Chẩn đoán<select value={researchForm.diagnosis} onChange={(event) => setResearchForm({ ...researchForm, diagnosis: event.target.value })}><option>Viêm quanh khớp vai thể giả liệt (ICD-10: M75.1)</option><option>Viêm quanh khớp vai thể đông cứng (ICD-10: M75.0)</option><option>Viêm quanh khớp vai thể đơn thuần (ICD-10: M75.8)</option><option>Viêm quanh khớp cấp (ICD-10: M75.3 / M75.5)</option><option>Viêm quanh khớp vai (P) (ICD-10: M75)</option></select></label>
                <label>Vị trí vai tổn thương<select value={researchForm.shoulder_side} onChange={(event) => setResearchForm({ ...researchForm, shoulder_side: event.target.value })}><option>Vai trái (1)</option><option>Vai phải (2)</option><option>Cả hai vai (3)</option></select></label>
                <label>Thời gian mắc bệnh<select value={researchForm.disease_duration} onChange={(event) => setResearchForm({ ...researchForm, disease_duration: event.target.value })}><option>&lt; 1 tháng (1)</option><option>1 - 3 tháng (2)</option><option>&gt;= 3 tháng (3)</option></select></label>
              </ResearchSection>
              <ResearchSection title="II. Thông tin phục hồi chức năng">
                <label>Bên tập luyện<select value={researchForm.training_side} onChange={(event) => setResearchForm({ ...researchForm, training_side: event.target.value })}><option>Vai trái</option><option>Vai phải</option><option>Cả hai vai</option></select></label>
                <label>Mức độ đau VAS<select value={researchForm.pain_level} onChange={(event) => setResearchForm({ ...researchForm, pain_level: event.target.value })}><option>Nhẹ (0-3)</option><option>Trung bình (4-6)</option><option>Nặng (7-10)</option></select></label>
                <label>Mức độ bệnh<select value={researchForm.severity} onChange={(event) => setResearchForm({ ...researchForm, severity: event.target.value })}><option>Nhẹ</option><option>Trung bình</option><option>Nặng</option></select></label>
              </ResearchSection>
              <ResearchSection title="III. Nội dung tập luyện được ghi hình">
                <label className="check-row"><input type="checkbox" checked={researchForm.exercise_codman} onChange={(event) => setResearchForm({ ...researchForm, exercise_codman: event.target.checked })} />Bài tập con lắc Codman</label>
                <label className="check-row"><input type="checkbox" checked={researchForm.exercise_pulley} onChange={(event) => setResearchForm({ ...researchForm, exercise_pulley: event.target.checked })} />Bài tập với gậy</label>
                <label className="check-row"><input type="checkbox" checked={researchForm.exercise_band} onChange={(event) => setResearchForm({ ...researchForm, exercise_band: event.target.checked })} />Bài tập với dây kháng lực</label>
              </ResearchSection>
              <ResearchSection title="IV. Đánh giá kỹ thuật động tác (Ground truth)">
                <label>Kết quả<select value={form.doctor_result} onChange={(event) => setForm({ ...form, doctor_result: event.target.value })}><option>Đúng</option><option>Sai</option><option>Gần đúng</option></select></label>
                <label>Tổng số lần thực hiện<input value={researchForm.total_reps} onChange={(event) => setResearchForm({ ...researchForm, total_reps: event.target.value })} inputMode="numeric" /></label>
                <label>Số lần đúng kỹ thuật<input value={researchForm.correct_reps} onChange={(event) => setResearchForm({ ...researchForm, correct_reps: event.target.value })} inputMode="numeric" /></label>
                <label>Chỉ định<select value={form.plan} onChange={(event) => setForm({ ...form, plan: event.target.value })}><option>Tiếp tục</option><option>Chuyển bài</option><option>Khám lại</option></select></label>
                <label className="span-two">
                  Lỗi sai
                  <div className="checkbox-grid">
                    {clinicalErrorOptions.map((option) => (
                      <label className="check-row" key={`research-${option}`}>
                        <input
                          type="checkbox"
                          checked={form.errors.includes(option)}
                          onChange={(event) => toggleClinicalError(option, event.target.checked)}
                        />
                        {option}
                      </label>
                    ))}
                  </div>
                </label>
                <label className="span-two">Nhận xét chuyên môn của Bác sĩ/KTV PHCN<textarea value={researchForm.specialist_comment} onChange={(event) => setResearchForm({ ...researchForm, specialist_comment: event.target.value })} /></label>
              </ResearchSection>
              <ResearchSection title="V. Thông tin dữ liệu video">
                <label>Mã video<input value={asText(selectedVideo.video_name)} readOnly /></label>
                <label>Thiết bị ghi hình<select value={researchForm.device} onChange={(event) => setResearchForm({ ...researchForm, device: event.target.value })}><option>Điện thoại</option><option>Webcam</option><option>Khác</option></select></label>
                <label>Khác, ghi rõ<input value={researchForm.device_other} onChange={(event) => setResearchForm({ ...researchForm, device_other: event.target.value })} /></label>
                <label>Góc quay<select value={researchForm.camera_angle} onChange={(event) => setResearchForm({ ...researchForm, camera_angle: event.target.value })}><option>Chính diện</option><option>Bên trái</option><option>Bên phải</option></select></label>
                <label>Khoảng cách camera (m)<input value={researchForm.camera_distance} onChange={(event) => setResearchForm({ ...researchForm, camera_distance: event.target.value })} inputMode="decimal" /></label>
              </ResearchSection>
              <ResearchSection title="VI. Xác nhận của người thu thập số liệu">
                <label className="check-row span-two"><input type="checkbox" checked={researchForm.collector_confirmed} onChange={(event) => setResearchForm({ ...researchForm, collector_confirmed: event.target.checked })} />Tôi xác nhận các thông tin và đánh giá trên được ghi nhận trung thực, dựa trên quan sát chuyên môn và/hoặc video ghi hình.</label>
                <label className="span-two">Kế hoạch theo dõi<textarea value={form.plan} onChange={(event) => setForm({ ...form, plan: event.target.value })} /></label>
                <label className="span-two">Ghi chú NCV/NCKH<input value={form.comments_ncv} onChange={(event) => setForm({ ...form, comments_ncv: event.target.value })} /></label>
              </ResearchSection>
              <button className="primary-btn" type="submit" disabled={!videos.length}>
                <ClipboardList size={18} aria-hidden="true" />
                Lưu & gửi phiếu NCKH
              </button>
            </form>
          ) : null}

          {subtab === "ai" ? (
            <div className="doctor-ai-panel">
              <section className="result-card doctor-video-review-card">
                <h3>Video bệnh nhân đã chọn</h3>
                {detail?.media.video_url ? (
                  <PhaseVideoPlayer
                    detail={detail}
                    src={mediaUrl(detail.media.video_url)}
                    poster={detail.frames[0]?.image_url ? mediaUrl(detail.frames[0].image_url) : undefined}
                    onPhaseChange={(value) => {
                      setFrameOffset(0);
                      setFramePhase(value);
                    }}
                  />
                ) : (
                  <div className="empty-state">Chưa tìm thấy video local.</div>
                )}
              </section>
              <div className="panel-grid">
              <section className="result-card">
                <h3>Phiếu đánh giá PHCN - Bác sĩ/KTV</h3>
                <DataTable rows={clinicalRows.slice(0, 8)} empty="Chưa có phiếu PHCN." columns={[{ key: "patient_username", label: "Bệnh nhân" }, { key: "doctor_result", label: "Kết quả" }, { key: "comments", label: "Nhận xét", wide: true }, { key: "time", label: "Thời gian" }]} />
              </section>
              <section className="result-card">
                <h3>Phiếu đánh giá NCV / AI</h3>
                <DataTable rows={researchRows.slice(0, 8)} empty="Chưa có phiếu NCV/AI." columns={[{ key: "patient_username", label: "Bệnh nhân" }, { key: "doctor_result", label: "Kết quả" }, { key: "comments_ncv", label: "Ghi chú", wide: true }, { key: "time", label: "Thời gian" }]} />
              </section>
              </div>
              {detail ? <AnalysisCharts chart={detail.chart} /> : null}
            </div>
          ) : null}

          {subtab === "media" ? (
            <div className="doctor-media-panel">
              {detail ? (
                <FrameGallery
                  token={token}
                  identifier={identifier}
                  detail={detail}
                  frameStart={frameStart}
                  frameEnd={frameEnd}
                  frameTotal={frameTotal}
                  framePage={framePage}
                  framePages={framePages}
                  canPrevFrames={frameStart > 0}
                  canNextFrames={frameEnd < frameTotal}
                  moveFramePage={moveFramePage}
                  goFramePage={goFramePage}
                  zoomFrame={zoomFrame}
                  setZoomFrame={setZoomFrame}
                  phase={framePhase}
                  status={frameStatus}
                  setPhase={(value) => {
                    setFrameOffset(0);
                    setFramePhase(value);
                  }}
                  setStatus={(value) => {
                    setFrameOffset(0);
                    setFrameStatus(value);
                  }}
                  showExportPanel={false}
                  onSaved={() => {
                    api
                      .videoDetail(token, identifier, frameOffset, frameLimit, framePhase, frameStatus, includeChart)
                      .then((data) => setDetail(data))
                      .catch(() => undefined);
                  }}
                />
              ) : null}
            </div>
          ) : null}
        </section>
      </div>
    </section>
  );
}

function PatientSymptomForm({ token, onSaved }: { token: string; onSaved: () => void }) {
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({
    vas: 3,
    pain_location: "",
    exercise: "Bài tập con lắc Codman",
    symptoms: "",
    date: today,
  });
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await api.createSymptom(token, form);
      setForm({ vas: 3, pain_location: "", exercise: "Bài tập con lắc Codman", symptoms: "", date: today });
      setMessage("Đã lưu khai báo.");
      onSaved();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể lưu khai báo.");
    }
  }

  return (
    <section className="panel">
      <div className="panel-title">
        <HeartPulse size={18} aria-hidden="true" />
        <h2>Thông tin khám & tập luyện</h2>
      </div>
      {message ? <div className="alert">{message}</div> : null}
      <form className="form-grid compact" onSubmit={submit}>
        <label>
          VAS: {form.vas}/10
          <input type="range" min="0" max="10" value={form.vas} onChange={(event) => setForm({ ...form, vas: Number(event.target.value) })} />
        </label>
        <label>
          Vị trí đau
          <input value={form.pain_location} onChange={(event) => setForm({ ...form, pain_location: event.target.value })} />
        </label>
        <label>
          Bài tập
          <select value={form.exercise} onChange={(event) => setForm({ ...form, exercise: event.target.value })}>
            <option>Bài tập con lắc Codman</option>
            <option>Bài tập với gậy (Pulley Exercise)</option>
            <option>Bài tập với dây kháng lực (Theraband Exercise)</option>
            <option>Khác</option>
          </select>
        </label>
        <label>
          Ngày
          <input type="date" value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} />
        </label>
        <label className="span-two">
          Triệu chứng
          <textarea value={form.symptoms} onChange={(event) => setForm({ ...form, symptoms: event.target.value })} />
        </label>
        <button className="primary-btn" type="submit">
          <ClipboardList size={18} aria-hidden="true" />
          Lưu khai báo
        </button>
      </form>
    </section>
  );
}

function PatientVideoUpload({ token, onSaved }: { token: string; onSaved: () => void }) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [exercise, setExercise] = useState("Bài tập con lắc Codman");
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setMessage("Chọn một file video trước khi tải lên.");
      return;
    }
    setUploading(true);
    setMessage("");
    try {
      await api.uploadVideo(token, file, exercise);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      setMessage("Đã tải video lên. NCV và Bác sĩ/KTV sẽ thấy video này để chạy phân tích.");
      onSaved();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không tải video lên được.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="panel upload-ready-panel">
      <div className="panel-title">
        <Upload size={18} aria-hidden="true" />
        <h2>Tải lên video tập luyện</h2>
      </div>
      <form className="patient-upload-form" onSubmit={submit}>
        <label className="upload-dropzone upload-dropzone-live">
          <Upload size={28} aria-hidden="true" />
          <strong>{file ? file.name : "Gửi video bài tập mới cho Bác sĩ/KTV và NCV"}</strong>
          <span>Video mới sẽ được lưu vào database, hiển thị trạng thái chờ phân tích và phát được như video thô.</span>
          <input
            ref={inputRef}
            type="file"
            accept="video/*,.mp4,.mov,.avi,.mkv,.webm"
            onChange={(event) => setFile(event.currentTarget.files?.[0] || null)}
          />
        </label>
        <label>
          Bài tập
          <select value={exercise} onChange={(event) => setExercise(event.target.value)}>
            <option>Bài tập con lắc Codman</option>
            <option>Bài tập với gậy (Pulley Exercise)</option>
            <option>Bài tập với dây kháng lực (Theraband Exercise)</option>
          </select>
        </label>
        <button className="primary-btn" type="submit" disabled={uploading || !file}>
          <Upload size={18} aria-hidden="true" />
          {uploading ? "Đang tải lên..." : "Lưu video"}
        </button>
        {message ? <div className={`alert ${message.includes("Không") || message.includes("Chọn") ? "error" : "success"}`}>{message}</div> : null}
      </form>
    </section>
  );
}

function AdminUsersView({
  payload,
  token,
  onRefresh,
}: {
  payload: DashboardPayload;
  token: string;
  onRefresh: () => void;
}) {
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    username: "",
    full_name: "",
    email: "",
    password: "",
    password2: "",
    role: "Bệnh nhân",
    must_change_password: false,
  });

  const filteredUsers = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return payload.users;
    return payload.users.filter((user) =>
      `${user.username} ${user.full_name} ${user.email} ${user.role}`.toLowerCase().includes(needle),
    );
  }, [payload.users, query]);

  async function createUser(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await api.createUser(token, form);
      setForm({
        username: "",
        full_name: "",
        email: "",
        password: "",
        password2: "",
        role: "Bệnh nhân",
        must_change_password: false,
      });
      setMessage("Đã tạo tài khoản.");
      onRefresh();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể tạo tài khoản.");
    }
  }

  async function toggleUser(user: User) {
    setMessage("");
    try {
      await api.setUserActive(token, user.username, !user.active);
      onRefresh();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể cập nhật tài khoản.");
    }
  }

  return (
    <section className="workspace-section">
      <div className="panel-grid admin-grid">
        <section className="panel">
          <div className="panel-title">
            <UserPlus size={18} aria-hidden="true" />
            <h2>Tạo tài khoản</h2>
          </div>
          {message ? <div className="alert">{message}</div> : null}
          <form className="form-grid compact" onSubmit={createUser}>
            <label>
              Tài khoản
              <input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
            </label>
            <label>
              Họ tên
              <input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
            </label>
            <label>
              Email
              <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </label>
            <label>
              Vai trò
              <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
                {roles.map((role) => (
                  <option key={role}>{role}</option>
                ))}
              </select>
            </label>
            <label>
              Mật khẩu
              <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
            </label>
            <label>
              Xác nhận mật khẩu
              <input type="password" value={form.password2} onChange={(event) => setForm({ ...form, password2: event.target.value })} />
            </label>
            <label className="check-row span-two">
              <input
                type="checkbox"
                checked={form.must_change_password}
                onChange={(event) => setForm({ ...form, must_change_password: event.target.checked })}
              />
              Buộc đổi mật khẩu lần đăng nhập sau
            </label>
            <button className="primary-btn" type="submit">
              <UserPlus size={18} aria-hidden="true" />
              Tạo user
            </button>
          </form>
        </section>
        <section className="panel wide-panel">
          <div className="panel-title with-search">
            <div>
              <Users size={18} aria-hidden="true" />
              <h2>Người dùng</h2>
            </div>
            <label className="search-box">
              <Search size={16} aria-hidden="true" />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm user" />
            </label>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Tài khoản</th>
                  <th>Họ tên</th>
                  <th>Email</th>
                  <th>Vai trò</th>
                  <th>Trạng thái</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.username}>
                    <td>{user.username}</td>
                    <td>{user.full_name}</td>
                    <td>{user.email || "N/A"}</td>
                    <td>
                      <span className={`role-pill ${roleClass(user.role)}`}>{user.role}</span>
                    </td>
                    <td>{user.active ? "Hoạt động" : "Đã khóa"}</td>
                    <td>
                      <button className="ghost-btn small" onClick={() => toggleUser(user)} type="button">
                        {user.active ? "Khóa" : "Mở"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </section>
  );
}

function InfoView({ payload, view }: { payload: DashboardPayload; view: ViewKey }) {
  const isPatient = payload.user.role_key === "patient";
  const initialInfoTab: "research" | "nckh" | "guide" | "team" | "contact" | "feedback" = isPatient
    ? view === "contact"
      ? "contact"
      : view === "feedback"
        ? "feedback"
        : "research"
    : view === "team"
      ? "team"
      : view === "contact"
        ? "contact"
      : view === "feedback"
        ? "feedback"
        : "nckh";
  const [activeInfoTab, setActiveInfoTab] = useState<"research" | "nckh" | "guide" | "team" | "contact" | "feedback">(initialInfoTab);
  useEffect(() => {
    setActiveInfoTab(initialInfoTab);
  }, [initialInfoTab]);
  const infoTabs = isPatient
    ? [
        ["research", "Trang thông tin nghiên cứu"],
        ["nckh", "Đề tài NCKH"],
        ["guide", "Hướng dẫn sử dụng"],
      ]
    : [
        ["nckh", "Đề tài NCKH"],
        ["guide", "Hướng dẫn sử dụng"],
        ["team", "Thành viên / hồ sơ đề tài"],
        ["contact", "Liên hệ"],
        ["feedback", "Góp ý & thảo luận"],
      ];
  const breadcrumbLabel =
    activeInfoTab === "team"
      ? "Hồ sơ đề tài & đội ngũ chuyên gia"
      : activeInfoTab === "feedback"
        ? "Phản hồi"
        : activeInfoTab === "contact"
          ? "Thông tin liên hệ"
          : activeInfoTab === "guide"
            ? "Hướng dẫn sử dụng"
            : activeInfoTab === "nckh"
              ? "Đề tài nghiên cứu khoa học"
              : isPatient
              ? "Trang thông tin nghiên cứu"
              : "Thông tin tổng hợp";
  const patientResearchSections: Array<{ title: string; body: ReactNode; open?: boolean; tone?: "warning" | "success" | "info" }> = [
    {
      title: "1. GIỚI THIỆU VỀ NGHIÊN CỨU",
      open: true,
      body: (
        <>
          <p>Nghiên cứu này nhằm thử nghiệm một hệ thống giúp theo dõi việc tập luyện phục hồi chức năng khớp vai bằng camera và máy tính. Hệ thống sẽ giúp ghi nhận và phân tích các động tác tập luyện của người bệnh.</p>
          <p>Đối tượng tham gia là người bệnh được chẩn đoán viêm quanh khớp vai đang điều trị tại Khoa Phục hồi chức năng – Bệnh viện Đa khoa Phạm Ngọc Thạch. Mục tiêu của nghiên cứu là đánh giá xem hệ thống có thể nhận biết và đánh giá đúng các động tác tập luyện hay không, từ đó hướng tới việc hỗ trợ theo dõi tập luyện từ xa trong tương lai.</p>
        </>
      ),
    },
    {
      title: "2. QUY TRÌNH NGHIÊN CỨU",
      body: (
        <>
          <p>Nghiên cứu được thực hiện từ tháng 12 năm 2025 đến tháng 7 năm 2026 tại Khoa Phục hồi chức năng – Bệnh viện Đa khoa Phạm Ngọc Thạch. Người tham gia là người bệnh viêm quanh khớp vai đang được chỉ định tập phục hồi chức năng. Dự kiến có khoảng 05 người bệnh tham gia.</p>
          <p>Người tham gia cần có khả năng thực hiện các bài tập theo hướng dẫn và đồng ý tham gia nghiên cứu. Những trường hợp không đủ điều kiện sức khỏe hoặc không thể phối hợp trong quá trình thực hiện sẽ không được tham gia.</p>
          <p>Trong quá trình tham gia, người bệnh sẽ thực hiện các bài tập phục hồi chức năng khớp vai theo hướng dẫn của nhân viên y tế, bao gồm bài tập con lắc, bài tập với gậy và bài tập với dây kháng lực. Quá trình tập luyện sẽ được ghi hình bằng thiết bị điện tử. Thông tin thu thập bao gồm video ghi lại quá trình tập luyện và một số thông tin cơ bản liên quan đến việc thực hiện động tác. Các video này sẽ được sử dụng để đánh giá mức độ chính xác của động tác và so sánh với nhận định của nhân viên y tế. Kết quả đánh giá sẽ được thông báo lại cho người bệnh để biết và điều chỉnh cách tập nếu cần.</p>
          <p>Mỗi lần tham gia kéo dài khoảng 5–10 phút và không làm ảnh hưởng đến thời gian điều trị thông thường của người bệnh.</p>
        </>
      ),
    },
    {
      title: "3. NGUY CƠ CÓ THỂ XẢY RA",
      tone: "warning",
      body: (
        <>
          <p>Người bệnh có thể cảm thấy mệt, đau cơ nhẹ hoặc căng cơ khi thực hiện các bài tập. Việc ghi hình có thể khiến một số người cảm thấy không thoải mái.</p>
          <p>Để giảm thiểu các nguy cơ này, người bệnh luôn có nhân viên y tế theo dõi. Dữ liệu (video) sẽ được mã hóa và bảo mật tuyệt đối.</p>
        </>
      ),
    },
    {
      title: "4. QUYỀN LỢI CỦA NGƯỜI THAM GIA",
      tone: "success",
      body: <p>Người tham gia không phải trả bất kỳ chi phí nào. Được nhân viên y tế hướng dẫn và theo dõi tập luyện để đảm bảo an toàn và đúng kỹ thuật.</p>,
    },
    {
      title: "5. BẢO MẬT VÀ LƯU TRỮ THÔNG TIN",
      body: <p>Toàn bộ thông tin và dữ liệu thu thập được bảo mật theo quy định. Dữ liệu được mã hóa và lưu trữ trong hệ thống an toàn; chỉ các thành viên được phân công mới có quyền truy cập. Thông tin cá nhân sẽ không được tiết lộ khi công bố kết quả.</p>,
    },
    {
      title: "6. TÍNH CHẤT TÌNH NGUYỆN",
      body: <p>Việc tham gia hoàn toàn tự nguyện. Người bệnh có quyền từ chối hoặc rút khỏi nghiên cứu bất cứ lúc nào mà không cần nêu lý do. Quyết định này không ảnh hưởng đến việc điều trị tại bệnh viện.</p>,
    },
    {
      title: "7. HÌNH THỨC CÔNG BỐ THÔNG TIN",
      body: <p>Kết quả có thể được sử dụng cho mục đích học tập, báo cáo khoa học hoặc hội thảo. Mọi thông tin cá nhân đều được bảo mật tuyệt đối.</p>,
    },
  ];
  const nckhSections: Array<{ title: string; body: ReactNode; open?: boolean }> = [
    {
      title: "📌 ĐẶT VẤN ĐỀ",
      open: true,
      body: (
        <>
          <p>Trong những năm gần đây, cùng với sự gia tăng của các bệnh lý cơ xương khớp, chấn thương thể thao và đột quỵ, nhu cầu phục hồi chức năng (PHCN) trên toàn thế giới ngày càng tăng cao.</p>
          <p>Theo Tổ chức Y tế Thế giới (WHO), hiện có khoảng 2,4 tỷ người cần ít nhất một hình thức phục hồi chức năng, chiếm gần một phần ba dân số toàn cầu. Tại Việt Nam, theo Hội Phục hồi chức năng Việt Nam (2023), có khoảng 7,06% dân số từ 2 tuổi trở lên là người khuyết tật, trong đó phần lớn cần được can thiệp PHCN.</p>
          <p>Mặc dù nhu cầu PHCN lớn, song năng lực cung cấp dịch vụ này tại Việt Nam vẫn còn hạn chế. Trung bình 10.000 người dân chỉ có 0,25 nhân viên phục hồi chức năng, thấp hơn đáng kể so với khuyến nghị của WHO là 0,5-1 người/10.000 dân. Thực tế này khiến nhiều bệnh nhân phải tự tập luyện tại nhà sau khi xuất viện mà thiếu sự giám sát chuyên môn.</p>
          <p>Xuất phát từ thực tiễn trên, nhóm nghiên cứu quyết định thực hiện đề tài: <strong>"Phát triển Mô hình thử nghiệm giám sát tập luyện Phục hồi chức năng từ xa dựa trên Trí tuệ nhân tạo (AI) và Thị giác máy tính (Computer Vision)"</strong>.</p>
        </>
      ),
    },
    {
      title: "🎯 MỤC TIÊU NGHIÊN CỨU",
      open: true,
      body: (
        <>
          <p><strong>Mục tiêu 1:</strong> Xây dựng mô hình nhận diện và đánh giá 3 bài tập phục hồi chức năng cho bệnh nhân viêm quanh khớp vai, bao gồm:</p>
          <ul>
            <li>Bài tập con lắc Codman</li>
            <li>Bài tập với gậy</li>
            <li>Bài tập với dây kháng lực</li>
          </ul>
          <p><strong>Mục tiêu 2:</strong> So sánh độ chính xác của mô hình với đánh giá thủ công trên một tập dữ liệu nhỏ.</p>
        </>
      ),
    },
    {
      title: "🔬 ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU",
      open: true,
      body: (
        <>
          <p><strong>Đối tượng nghiên cứu:</strong> 05 bệnh nhân viêm quanh khớp vai + nhóm chuyên gia PHCN tại Khoa Phục hồi chức năng, Bệnh viện Đa khoa Phạm Ngọc Thạch.</p>
          <p><strong>Thiết kế nghiên cứu:</strong> Nghiên cứu định lượng, phát triển mô hình học máy.</p>
          <p><strong>Công nghệ sử dụng:</strong></p>
          <ul>
            <li>MediaPipe Pose Estimation cho ước lượng tư thế</li>
            <li>Python và các thư viện xử lý ảnh (OpenCV, NumPy, Pandas)</li>
            <li>Streamlit cho giao diện người dùng</li>
            <li>Plotly cho trực quan hóa dữ liệu</li>
          </ul>
          <p><strong>Cỡ mẫu dự kiến:</strong> 500-1000 chuỗi chuyển động.</p>
        </>
      ),
    },
    {
      title: "📊 KẾT QUẢ DỰ KIẾN",
      open: true,
      body: (
        <div className="expected-metrics-grid compact">
          <div><span>Độ chính xác (Accuracy)</span><strong>≥ 90%</strong></div>
          <div><span>F1-Score</span><strong>≥ 0.85</strong></div>
          <div><span>Sai số MAE</span><strong>&lt; 5°</strong></div>
          <div><span>Hệ số ICC</span><strong>≥ 0.75</strong></div>
          <div><span>Precision</span><strong>≥ 0.85</strong></div>
          <div><span>Recall</span><strong>≥ 0.85</strong></div>
        </div>
      ),
    },
    {
      title: "🎁 ĐÓNG GÓP CỦA ĐỀ TÀI",
      open: true,
      body: (
        <ul>
          <li><strong>Về khoa học và đào tạo:</strong> Xây dựng mô hình nhận diện động tác PHCN, tạo bộ dữ liệu chuẩn hóa, là tài liệu thực hành cho sinh viên ngành Khoa học dữ liệu y sinh.</li>
          <li><strong>Về phát triển kinh tế:</strong> Giảm chi phí đi lại, giảm tải cho nhân viên y tế, tối ưu nguồn lực bệnh viện.</li>
          <li><strong>Về xã hội:</strong> Tăng khả năng tiếp cận dịch vụ PHCN, thúc đẩy chuyển đổi số y tế, xây dựng hệ thống chăm sóc sức khỏe thông minh.</li>
        </ul>
      ),
    },
    {
      title: "📚 TÀI LIỆU THAM KHẢO",
      body: (
        <ol>
          <li>WHO. Rehabilitation 2030: A call for action.</li>
          <li>Cieza A, et al. Global estimates of the need for rehabilitation. Lancet. 2021.</li>
          <li>Lugaresi C, et al. MediaPipe: A Framework for Building Perception Pipelines. arXiv. 2019.</li>
          <li>Cao Z, et al. OpenPose: Realtime Multi-Person 2D Pose Estimation. arXiv. 2019.</li>
          <li>Hellstén T, et al. Reliability and validity of computer vision-based markerless human pose estimation. Healthc Technol Lett. 2025.</li>
          <li>Ino T, et al. Validity and Reliability of OpenPose-Based Motion Analysis. J Sports Sci Med. 2024.</li>
          <li>Aguilar-Ortega R, et al. UCO Physical Rehabilitation: New Dataset and Study. Sensors. 2023.</li>
          <li>Nguyễn Thị Ngọc Lan, et al. Thực trạng nhu cầu phục hồi chức năng tại Việt Nam. Tạp chí Y học Việt Nam. 2024.</li>
        </ol>
      ),
    },
  ];
  const teamMembers = [
    ["Kim Mạnh Hùng", "Thành viên", "CNCQ KHDL1-1A", "2211090016@studenthuph.edu.vn"],
    ["Nguyễn Hải An", "Thành viên", "CNCQ KHDL1-1A", "2211090001@studenthuph.edu.vn"],
    ["Phan Vân Anh", "Thành viên", "CNCQ KHDL1-1A", "2211090004@studenthuph.edu.vn"],
    ["Nguyễn Thị Thanh Nga", "Thành viên", "CNCQ KHDL1-1A", "2211090027@studenthuph.edu.vn"],
    ["Nguyễn Thị Thơm", "Thành viên nghiên cứu", "CNCQ KTPHCN3-1A", "2216030122@studenthuph.edu.vn"],
    ["Nguyễn Thị Thu Hương", "Thành viên nghiên cứu", "CNCQ YTCC22-1A", "2317010071@studenthuph.edu.vn"],
  ];
  return (
    <section className="workspace-section">
      <div className="info-breadcrumb">📍 Đang xem: <b>{breadcrumbLabel}</b></div>
      <div className="info-tabs-row" role="tablist" aria-label="Thông tin tổng hợp">
        {infoTabs.map(([key, label]) => (
          <button key={key} type="button" className={activeInfoTab === key ? "active" : ""} onClick={() => setActiveInfoTab(key as typeof activeInfoTab)}>
            {label}
          </button>
        ))}
      </div>
      <div className="panel-grid info-panel-grid">
        {activeInfoTab === "feedback" ? (
          <section className="panel wide-panel feedback-panel">
            <div className="panel-title with-search">
              <div>
                <ClipboardList size={18} aria-hidden="true" />
                <h2>Cộng đồng Rehab-AI: góp ý & thảo luận</h2>
              </div>
              <span className="role-pill patient">Phản hồi vận hành</span>
            </div>
            <div className="feedback-layout">
              <form className="form-grid">
                <label>
                  Tên của bạn
                  <input value={payload.user.full_name || payload.user.username} readOnly />
                </label>
                <label>
                  Nội dung góp ý/thảo luận
                  <textarea placeholder="Ghi lại lỗi gặp phải, đề xuất cải tiến hoặc nội dung cần nhóm triển khai hỗ trợ..." />
                </label>
                <button className="ghost-btn" type="button">
                  Gửi bình luận
                </button>
              </form>
              <div className="feedback-recent">
                <h3>Thảo luận gần đây</h3>
                <div className="empty-state">Chưa có bình luận nào trong dữ liệu React. Hãy là người đầu tiên để lại ý kiến.</div>
              </div>
            </div>
          </section>
        ) : null}
        {activeInfoTab === "research" ? (
          <section className="panel wide-panel research-accordion-panel patient-research-page">
            <div className="panel-title">
              <FileText size={18} aria-hidden="true" />
              <h2>Trang thông tin nghiên cứu</h2>
            </div>
            <div className="patient-research-heading">
              <b>Trang thông tin nghiên cứu</b>
              <h3>PHÁT TRIỂN MÔ HÌNH THỬ NGHIỆM GIÁM SÁT TẬP LUYỆN PHỤC HỒI CHỨC NĂNG TỪ XA DỰA TRÊN TRÍ TUỆ NHÂN TẠO VÀ THỊ GIÁC MÁY TÍNH TẠI BỆNH VIỆN ĐA KHOA PHẠM NGỌC THẠCH - TRƯỜNG ĐẠI HỌC Y TẾ CÔNG CỘNG (2025–2026)</h3>
              <p>Dành cho đối tượng: Người bệnh viêm quanh khớp vai điều trị tại Khoa Phục hồi chức năng</p>
            </div>
            <div className="research-accordion patient-research-accordion">
              {patientResearchSections.map((section) => (
                <details key={section.title} open={section.open} className={section.tone ? `tone-${section.tone}` : ""}>
                  <summary>{section.title}</summary>
                  <div className="research-detail-body">{section.body}</div>
                </details>
              ))}
            </div>
          </section>
        ) : null}
        {activeInfoTab === "nckh" ? (
          <section className="panel wide-panel research-accordion-panel nckh-page">
            <div className="nckh-title-box">
              <b>ĐỀ TÀI NGHIÊN CỨU KHOA HỌC</b>
              <span>Phát triển Mô hình thử nghiệm giám sát tập luyện Phục hồi chức năng từ xa</span>
              <p>Dựa trên Trí tuệ nhân tạo (AI) và Thị giác máy tính (Computer Vision)</p>
              <small>Bệnh viện Đa khoa Phạm Ngọc Thạch - Trường Đại học Y tế Công cộng (2025-2026)</small>
            </div>
            <div className="research-accordion nckh-accordion">
              {nckhSections.map((section) => (
                <details key={section.title} open={section.open}>
                  <summary>{section.title}</summary>
                  <div className="research-detail-body">{section.body}</div>
                </details>
              ))}
            </div>
          </section>
        ) : null}
        {activeInfoTab === "guide" ? (
          isPatient ? (
            <section className="panel wide-panel patient-upload-guide-panel">
              <div className="panel-title">
                <Upload size={18} aria-hidden="true" />
                <h2>Hướng dẫn bệnh nhân quay và upload video</h2>
              </div>
              <p className="info-copy">
                Người bệnh chỉ cần quay video bài tập theo hướng dẫn của nhân viên y tế, sau đó tải video lên tại Trang chủ để nhóm NCV/Bác sĩ xem và phản hồi.
              </p>
              <div className="patient-guide-steps">
                {[
                  ["1", "Chuẩn bị không gian", "Đặt điện thoại cố định cách người tập khoảng 2-3 mét, đủ sáng, thấy rõ toàn thân và vùng vai."],
                  ["2", "Quay đúng bài tập", "Chọn bài tập được hướng dẫn trên Trang chủ, quay chính diện, không mặc áo quá rộng hoặc quá tối màu."],
                  ["3", "Chọn file video", "Sau khi quay xong, vào Trang chủ, kéo tới mục tải video và chọn file MP4, MOV, AVI, MKV từ máy/điện thoại."],
                  ["4", "Upload lên hệ thống", "Bấm gửi video. Giữ nguyên màn hình cho tới khi hệ thống báo đã lưu video thành công."],
                  ["5", "Theo dõi kết quả", "Sau khi NCV hoặc Bác sĩ/KTV xử lý, mở tab Kết quả đánh giá để xem nhận xét, video, biểu đồ và frame AI."],
                ].map(([step, title, text]) => (
                  <article key={step}>
                    <b>{step}</b>
                    <div>
                      <strong>{title}</strong>
                      <span>{text}</span>
                    </div>
                  </article>
                ))}
              </div>
              <div className="patient-guide-note">
                <AlertCircle size={18} aria-hidden="true" />
                <span>Nếu đang đau tăng, chóng mặt, tê yếu bất thường hoặc không chắc cách tập, hãy dừng quay và liên hệ nhân viên y tế trước khi upload.</span>
              </div>
            </section>
          ) : (
            <>
              <section className="panel info-feature-card">
                <div className="panel-title">
                  <HeartPulse size={18} aria-hidden="true" />
                  <h2>Hướng dẫn theo vai trò</h2>
                </div>
                <div className="info-list">
                  <span>Bệnh nhân: khai báo triệu chứng, xem kết quả, video, biểu đồ và lịch nhắc.</span>
                  <span>Bác sĩ/KTV: theo dõi video, phiếu đánh giá, nhận xét lâm sàng và lịch nhắc.</span>
                  <span>NCV: xem dữ liệu nghiên cứu, frame gallery, chỉ số ML và đồng bộ artifact.</span>
                  <span>Quản trị viên: quản lý tài khoản, audit dữ liệu và điều phối phân tích AI.</span>
                </div>
              </section>
              <section className="panel info-feature-card">
                <div className="panel-title">
                  <Stethoscope size={18} aria-hidden="true" />
                  <h2>Kiến thức PHCN</h2>
                </div>
                <p className="info-copy">
                  Hệ thống tập trung vào bài tập con lắc Codman, bài tập với gậy và theo dõi biên độ vận động vai bằng video tại nhà. Kết quả AI là dữ liệu hỗ trợ, cần đối chiếu với đánh giá chuyên môn.
                </p>
                <div className="info-list">
                  <span>4 trụ cột của y tế hiện đại: Phòng bệnh, Điều trị, Phục hồi chức năng, Nâng cao sức khỏe.</span>
                  <span>Lợi ích PHCN: hồi phục tối đa chức năng suy yếu, ngăn ngừa teo cơ/cứng khớp, hỗ trợ tự lập trong sinh hoạt hằng ngày và giảm gánh nặng chăm sóc dài hạn.</span>
                  <span>Quy trình PHCN chuẩn: lượng giá chức năng, lập kế hoạch điều trị, thực hiện và theo dõi, đánh giá và duy trì tập luyện tại nhà.</span>
                  <span>Nguồn tham khảo: Cục Quản lý Khám chữa bệnh - Bộ Y tế, WHO Rehabilitation Topics, WHO Rehabilitation 2030.</span>
                </div>
              </section>
              <section className="panel info-feature-card">
                <div className="panel-title">
                  <FlaskConical size={18} aria-hidden="true" />
                  <h2>Công nghệ AI</h2>
                </div>
                <div className="info-list">
                  <span>MediaPipe pose để trích xuất khung xương và góc khớp.</span>
                  <span>Google MediaPipe/BlazePose theo dõi 33 body landmarks và hỗ trợ ước lượng tư thế theo thời gian thực.</span>
                  <span>Telerehabilitation giúp bệnh nhân ở xa tiếp cận giám sát tập luyện, giảm chi phí đi lại và tăng khả năng cá nhân hóa phác đồ.</span>
                  <span>Biểu đồ line, histogram, boxplot, pie và radar cho chỉ số nghiên cứu.</span>
                  <span>Frame gallery hỗ trợ xem khung lớn và phân trang toàn bộ frame.</span>
                  <span>Job phân tích có trạng thái start/rerun/retry/cancel cho admin/NCV.</span>
                </div>
              </section>
            </>
          )
        ) : null}
        {activeInfoTab === "team" && !isPatient ? (
          <section className="panel wide-panel research-project-panel">
            <div className="panel-title">
              <FileText size={18} aria-hidden="true" />
              <h2>Thông tin đề tài & đội ngũ nghiên cứu</h2>
            </div>
            <div className="research-story">
              <div className="research-title-box dynamic">
                <b>Đề tài nghiên cứu khoa học</b>
                <span>Phát triển mô hình thử nghiệm giám sát tập luyện Phục hồi chức năng từ xa</span>
                <span>Dựa trên Trí tuệ nhân tạo (AI) và Thị giác máy tính (Computer Vision)</span>
                <span>Bệnh viện Đa khoa Phạm Ngọc Thạch - Trường Đại học Y tế Công cộng (2025-2026)</span>
              </div>
              <details open>
                <summary>Bối cảnh</summary>
                <p>Trong những năm gần đây, nhu cầu phục hồi chức năng tăng cao trong khi năng lực cung cấp dịch vụ còn hạn chế. Hệ thống hỗ trợ người bệnh tự tập tại nhà nhưng vẫn có giám sát chuyên môn.</p>
              </details>
              <details>
                <summary>Mục tiêu nghiên cứu</summary>
                <p>Xây dựng mô hình nhận diện và đánh giá ba bài tập phục hồi chức năng khớp vai: Codman, bài tập với gậy và bài tập với dây kháng lực; so sánh độ chính xác của mô hình với đánh giá thủ công.</p>
              </details>
              <details>
                <summary>Phương pháp nghiên cứu</summary>
                <p>Video tập luyện được xử lý bằng MediaPipe/BlazePose, trích xuất 33 landmarks, tính góc vai và khuỷu, đối chiếu với video YouTube mẫu và tổng hợp thành biểu đồ/chỉ số nghiên cứu.</p>
              </details>
            </div>
            <div className="team-showcase">
              <h3>👨‍🏫 Giảng viên hướng dẫn</h3>
              <div className="mentor-grid">
                <article><b>TS. Trần Hồng Việt 🎓</b><span>Giảng viên hướng dẫn Khoa học Dữ liệu</span><small>thviet79@gmail.com</small></article>
                <article><b>Cô Nguyễn Thị Thùy Chi 🎓</b><span>Giảng viên hướng dẫn Lâm sàng</span><small>chi.ntt@huph.edu.vn</small></article>
              </div>
              <h3>👩‍⚕️ Chủ nhiệm đề tài</h3>
              <article className="owner-card"><b>Đinh Lê Quỳnh Phương 🛡️</b><span>Chủ nhiệm đề tài · MSSV: 2211090031</span><small>2211090031@studenthuph.edu.vn</small></article>
              <h3>👥 Thành viên nghiên cứu</h3>
              <div className="member-grid">
                {teamMembers.map(([name, role, cls, email]) => (
                  <article key={email}>
                    <b>{name} 🛡️</b>
                    <span>{role}</span>
                    <strong>{cls}</strong>
                    <small>{email}</small>
                  </article>
                ))}
              </div>
              <h3>🏥 Đơn vị phối hợp</h3>
              <div className="partner-card">
                <b>Bệnh viện Đa khoa Phạm Ngọc Thạch</b>
                <span>Khoa Phục hồi chức năng</span>
                <small>Địa chỉ: 1A Đ. Đức Thắng, Đông Ngạc, Hà Nội</small>
              </div>
            </div>
          </section>
        ) : null}
        {activeInfoTab === "contact" ? (
          <section className="panel wide-panel contact-dynamic-panel">
            <div className="panel-title">
              <Mail size={18} aria-hidden="true" />
              <h2>Thông tin liên hệ</h2>
            </div>
            <div className="contact-card-grid">
              <article className="contact-card cyan">
                <h3>Nghiên cứu viên chính</h3>
                <p>Họ tên: Đinh Lê Quỳnh Phương</p>
                <p>Địa chỉ: 1A Đức Thắng, phường Đông Ngạc, Hà Nội</p>
                <a href="mailto:2211090031@studenthuph.edu.vn">2211090031@studenthuph.edu.vn</a>
                <strong>0382665916</strong>
              </article>
              <article className="contact-card red">
                <h3>Hội đồng đạo đức</h3>
                <p>Tên: HĐĐĐ Trường ĐH Y tế Công cộng</p>
                <p>Địa chỉ: 1A Đức Thắng, phường Đông Ngạc, Hà Nội</p>
                <a href="mailto:irb@huph.edu.vn">irb@huph.edu.vn</a>
                <strong>024 62663024</strong>
              </article>
            </div>
            <section className="map-panel">
              <div>
                <h3>📍 Vị trí Bệnh viện Đa khoa Phạm Ngọc Thạch</h3>
                <a className="primary-btn" href="https://www.google.com/maps/search/?api=1&query=Benh%20vien%20Da%20khoa%20Pham%20Ngoc%20Thach%20Ha%20Noi" target="_blank" rel="noreferrer">
                  Xem trên Google Maps
                </a>
              </div>
              <p>1A Đức Thắng, phường Đông Ngạc, Hà Nội</p>
              <iframe title="Bản đồ Bệnh viện Đa khoa Phạm Ngọc Thạch" src="https://www.google.com/maps?q=Tr%C6%B0%E1%BB%9Dng%20%C4%90%E1%BA%A1i%20h%E1%BB%8Dc%20Y%20t%E1%BA%BF%20C%C3%B4ng%20c%E1%BB%99ng%20H%C3%A0%20N%E1%BB%99i&output=embed" loading="lazy" />
            </section>
          </section>
        ) : null}
        {activeInfoTab === "team" && !isPatient ? (
          <section className="panel info-feature-card">
          <div className="panel-title">
            <Users size={18} aria-hidden="true" />
            <h2>Hồ sơ đề tài</h2>
          </div>
          <dl className="kv-list">
            <div>
              <dt>Đơn vị</dt>
              <dd>HUPH × Bệnh viện Phạm Ngọc Thạch</dd>
            </div>
            <div>
              <dt>Giảng viên hướng dẫn 1</dt>
              <dd>TS. Trần Hồng Việt</dd>
            </div>
            <div>
              <dt>Giảng viên hướng dẫn 2</dt>
              <dd>Nguyễn Thị Thùy Chi</dd>
            </div>
            <div>
              <dt>Chủ nhiệm đề tài</dt>
              <dd>Đinh Lê Quỳnh Phương</dd>
            </div>
            <div>
              <dt>Thành viên nghiên cứu</dt>
              <dd>Kim Mạnh Hưng, Nguyễn Hải An, Phan Vân Anh, Nguyễn Thị Thanh Nga, Nguyễn Thị Thơm, Nguyễn Thị Thu Hương</dd>
            </div>
            <div>
              <dt>Đơn vị phối hợp</dt>
              <dd>Bệnh viện Đa khoa Phạm Ngọc Thạch - Khoa Phục hồi chức năng</dd>
            </div>
          </dl>
        </section>
        ) : null}
      </div>
    </section>
  );
}

function Shell({
  payload,
  token,
  onLogout,
  onRefresh,
  theme,
  onToggleTheme,
}: {
  payload: DashboardPayload;
  token: string;
  onLogout: () => void;
  onRefresh: () => void;
  theme: ThemeMode;
  onToggleTheme: () => void;
}) {
  const nav = roleTabs(payload.user.role_key, payload.metrics.videos > 0);
  const [active, setActive] = useState<ViewKey>(() => defaultTabForRole(payload.user.role_key));
  const [isCompactSidebar, setIsCompactSidebar] = useState(() => (typeof window === "undefined" ? false : window.matchMedia("(max-width: 1040px)").matches));
  const [sidebarOpen, setSidebarOpen] = useState(() => (typeof window === "undefined" ? true : !window.matchMedia("(max-width: 1040px)").matches));
  const [isViewPending, startViewTransition] = useTransition();
  const selectView = (view: ViewKey) => {
    startViewTransition(() => setActive(view));
    if (isCompactSidebar) {
      setSidebarOpen(false);
    }
  };

  useEffect(() => {
    if (!nav.some((item) => item.key === active)) {
      setActive(defaultTabForRole(payload.user.role_key));
    }
  }, [active, nav, payload.user.role_key]);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 1040px)");
    const syncSidebarMode = () => {
      const compact = media.matches;
      setIsCompactSidebar(compact);
      setSidebarOpen(compact ? false : true);
    };
    syncSidebarMode();
    media.addEventListener("change", syncSidebarMode);
    return () => media.removeEventListener("change", syncSidebarMode);
  }, []);

  return (
    <main className={`app-shell ${sidebarOpen ? "sidebar-is-open" : "sidebar-collapsed"}`}>
      {sidebarOpen ? (
        <>
          <button className="sidebar-backdrop" type="button" aria-label="Đóng menu" onClick={() => setSidebarOpen(false)} />
          <SidebarInfo payload={payload} nav={nav} active={active} onSelect={selectView} onCollapse={() => setSidebarOpen(false)} />
        </>
      ) : null}
      <section className={`main-area ${isViewPending ? "view-pending" : ""}`}>
        <header className="topbar">
          <div className="topbar-brand">
            <button className="sidebar-open-btn" type="button" onClick={() => setSidebarOpen((current) => !current)} title={sidebarOpen ? "Thu sidebar" : "Mở sidebar"}>
              {sidebarOpen ? <PanelLeftClose size={18} aria-hidden="true" /> : <PanelLeftOpen size={18} aria-hidden="true" />}
            </button>
            <div className="brand-mark small">
              <HeartPulse size={22} aria-hidden="true" />
            </div>
            <div>
              <strong>
                Rehab <b>AI</b> Monitor
              </strong>
              <span>Hệ sinh thái lâm sàng · HUPH × BV Phạm Ngọc Thạch · 2026</span>
            </div>
          </div>
          <div className="topbar-actions">
            <span className={`topbar-role role-pill ${roleClass(payload.user.role)}`}>
              {(() => {
                const RoleIcon = roleIconFor(payload.user.role_key);
                return <RoleIcon size={15} aria-hidden="true" />;
              })()}
              {roleNames[payload.user.role_key]}
            </span>
            <div className="topbar-userchip">
              <div className="topbar-avatar">{avatarInitials(payload.user.full_name || payload.user.username)}</div>
              <div>
                <strong>{payload.user.full_name || payload.user.username}</strong>
                <span>{payload.user.username}</span>
              </div>
            </div>
            <button className="topbar-icon-btn" onClick={onRefresh} type="button" title="Làm mới dữ liệu">
              <RefreshCw size={18} aria-hidden="true" />
            </button>
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            <button className="topbar-icon-btn" onClick={onLogout} type="button" title="Đăng xuất">
              <LogOut size={18} aria-hidden="true" />
            </button>
          </div>
        </header>
        {active === "home" ? <Overview payload={payload} token={token} onSaved={onRefresh} onNavigate={selectView} /> : null}
        {active === "admin_video" ? <AdminVideoWorkspace payload={payload} token={token} /> : null}
        {active === "admin_research" ? <AdminResearchWorkspace payload={payload} /> : null}
        {active === "patient_results" ? <VideoResultWorkspace payload={payload} token={token} title="Kết quả đánh giá" /> : null}
        {active === "research_results" ? <VideoResultWorkspace payload={payload} token={token} title="Kết quả đánh giá" /> : null}
        {active === "research_analysis" ? (
          <VideoResultWorkspace
            payload={payload}
            token={token}
            title="Phân tích & trích xuất dữ liệu"
            controls={(video, detail, reload) => (
              <AnalysisJobControls payload={payload} token={token} video={video} detail={detail} onReload={reload} />
            )}
          />
        ) : null}
        {active === "evaluation_forms" ? <EvaluationFormsView payload={payload} token={token} onSaved={onRefresh} /> : null}
        {active === "admin_panel" ? <AdminUsersView payload={payload} token={token} onRefresh={onRefresh} /> : null}
        {active === "patient_schedule" ? <PatientDataView payload={payload} token={token} onSaved={onRefresh} /> : null}
        {active === "admin_info" || active === "info" || active === "team" || active === "contact" || active === "feedback" ? <InfoView payload={payload} view={active} /> : null}
        <MainFooter />
      </section>
    </main>
  );
}

function MainFooter() {
  return (
    <footer className="main-footer">
      <div className="footer-container">
        <section className="footer-col">
          <div className="footer-brand-row">
            <div className="footer-logo-pulse">
              <img src="/logos/huph-logo.png" alt="Logo Trường Đại học Y tế Công cộng" />
            </div>
            <h3>Trường Đại học Y tế Công cộng</h3>
          </div>
          <p>1A Đức Thắng, phường Đông Ngạc, Hà Nội</p>
          <a href="https://huph.edu.vn/" target="_blank" rel="noreferrer">huph.edu.vn</a>
        </section>
        <section className="footer-col">
          <div className="footer-brand-row">
            <div className="footer-logo-pulse green">
              <img src="/logos/pnt_bv.jpg" alt="Logo Bệnh viện Đa khoa Phạm Ngọc Thạch" />
            </div>
            <h3>Bệnh viện Đa khoa Phạm Ngọc Thạch</h3>
          </div>
          <p>Khoa Vật lý trị liệu - Phục hồi chức năng</p>
          <a href="https://bvdkphamngocthach.vn" target="_blank" rel="noreferrer">bvdkphamngocthach.vn</a>
        </section>
        <section className="footer-col wide">
          <h3>Mục tiêu & công nghệ cốt lõi</h3>
          <p>Ứng dụng Computer Vision và MediaPipe AI để số hóa quy trình giám sát phục hồi chức năng từ xa, hỗ trợ bác sĩ/KTV đối chiếu video, biểu đồ và khung xương.</p>
        </section>
        <section className="footer-col">
          <h3>Hội đồng đạo đức</h3>
          <p>Trường Đại học Y tế Công cộng</p>
          <p>irb@huph.edu.vn · 024 62663024</p>
        </section>
      </div>
      <div className="footer-bottom">Đề tài NCKH cấp Trường | REHAB-AI-MONITOR | © 2026 Nhóm nghiên cứu Trường Đại học Y tế Công cộng</div>
    </footer>
  );
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(tokenKey) || "");
  const [theme, setTheme] = useState<ThemeMode>(() => (localStorage.getItem(themeKey) === "dark" ? "dark" : "light"));
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(Boolean(token));
  const [message, setMessage] = useState("");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(themeKey, theme);
  }, [theme]);

  useEffect(() => {
    const handleAuthExpired = () => {
      localStorage.removeItem(tokenKey);
      setToken("");
      setPayload(null);
      setMessage("");
      setLoading(false);
    };
    window.addEventListener("rehab-auth-expired", handleAuthExpired);
    return () => window.removeEventListener("rehab-auth-expired", handleAuthExpired);
  }, []);

  const toggleTheme = () => setTheme((current) => (current === "dark" ? "light" : "dark"));

  async function loadDashboard(nextToken = token) {
    if (!nextToken) return;
    setLoading(true);
    setMessage("");
    try {
      const dashboard = await api.dashboard(nextToken);
      setPayload(dashboard);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Không thể tải dữ liệu.");
      localStorage.removeItem(tokenKey);
      setToken("");
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadDashboard(token);
    }
  }, []);

  function handleAuth(auth: AuthResponse) {
    setToken(auth.token);
    void loadDashboard(auth.token);
  }

  async function handleLogout() {
    if (token) {
      try {
        await api.logout(token);
      } catch {
        // The local session is cleared even if the backend token is already gone.
      }
    }
    localStorage.removeItem(tokenKey);
    setToken("");
    setPayload(null);
  }

  if (!token) {
    return <AuthScreen onAuth={handleAuth} theme={theme} onToggleTheme={toggleTheme} />;
  }
  if (loading && !payload) {
    return (
      <main className="loading-screen">
        <RefreshCw size={28} className="spin" aria-hidden="true" />
        <span>Đang tải dữ liệu...</span>
      </main>
    );
  }
  if (message && !payload) {
    return (
      <main className="loading-screen">
        <div className="alert error">{message}</div>
        <button className="primary-btn" onClick={handleLogout} type="button">
          Về đăng nhập
        </button>
      </main>
    );
  }
  if (!payload) return null;
  return <Shell payload={payload} token={token} onLogout={handleLogout} onRefresh={() => void loadDashboard(token)} theme={theme} onToggleTheme={toggleTheme} />;
}

