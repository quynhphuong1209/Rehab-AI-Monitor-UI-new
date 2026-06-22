import type {
  AnalysisJob,
  AnalysisJobActionResult,
  AnalysisJobOptions,
  AnalysisJobStartResult,
  ApiErrorBody,
  AuthResponse,
  ChartExportResult,
  DashboardPayload,
  LoginOptionsPayload,
  LatestVideoBundleResult,
  User,
  VideoDetailPayload,
  VideoExportResult,
  VideoUploadResult,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

type RequestOptions = {
  token?: string | null;
  method?: string;
  body?: unknown;
  timeoutMs?: number;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  const controller = typeof AbortController !== "undefined" && options.timeoutMs ? new AbortController() : null;
  const timeout = controller ? window.setTimeout(() => controller.abort(), options.timeoutMs) : null;
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: options.method || "GET",
      headers,
      cache: "no-store",
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: controller?.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("Backend dang ban phan tich, tu cap nhat lai sau vai giay.", 408);
    }
    throw error;
  } finally {
    if (timeout) window.clearTimeout(timeout);
  }
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const body = data as ApiErrorBody;
    if (response.status === 401 && options.token && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("rehab-auth-expired"));
    }
    throw new ApiError(body.detail || "Yêu cầu chưa thực hiện được.", response.status);
  }
  return data as T;
}

async function uploadRequest<T>(path: string, token: string, body: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const errorBody = data as ApiErrorBody;
    if (response.status === 401 && token && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("rehab-auth-expired"));
    }
    throw new ApiError(errorBody.detail || "Khong upload duoc video.", response.status);
  }
  return data as T;
}

export const api = {
  baseUrl: API_BASE,
  loginOptions() {
    return request<LoginOptionsPayload>("/auth/login-options");
  },
  login(username: string, password: string) {
    return request<AuthResponse>("/auth/login", {
      method: "POST",
      body: { username, password },
    });
  },
  register(payload: {
    username: string;
    email: string;
    full_name: string;
    password: string;
    password2: string;
  }) {
    return request<{ ok: true; user: User }>("/auth/register", {
      method: "POST",
      body: payload,
    });
  },
  resetPassword(payload: {
    username: string;
    email: string;
    password: string;
    password2: string;
  }) {
    return request<{ ok: true; message: string }>("/auth/reset-password", {
      method: "POST",
      body: payload,
    });
  },
  logout(token: string) {
    return request<{ ok: true }>("/auth/logout", {
      method: "POST",
      token,
    });
  },
  me(token: string) {
    return request<{ user: User }>("/auth/me", { token });
  },
  dashboard(token: string) {
    return request<DashboardPayload>("/dashboard", { token });
  },
  videoDetail(token: string, identifier: string | number, frameOffset = 0, frameLimit = 48, framePhase = "all", frameStatus = "ALL") {
    const params = new URLSearchParams({
      frame_offset: String(frameOffset),
      frame_limit: String(frameLimit),
      frame_phase: framePhase,
      frame_status: frameStatus,
    });
    return request<VideoDetailPayload>(`/videos/${encodeURIComponent(String(identifier))}/detail?${params.toString()}`, { token });
  },
  startAnalysisJob(token: string, identifier: string | number, options: AnalysisJobOptions) {
    return request<AnalysisJobStartResult>(`/videos/${encodeURIComponent(String(identifier))}/analysis-jobs`, {
      token,
      method: "POST",
      body: options,
    });
  },
  latestAnalysisJob(token: string, identifier: string | number) {
    return request<{ job: AnalysisJob | null }>(
      `/videos/${encodeURIComponent(String(identifier))}/analysis-jobs/latest?_=${Date.now()}`,
      { token, timeoutMs: 2500 },
    );
  },
  analysisJobHistory(token: string, identifier: string | number) {
    return request<{ items: AnalysisJob[]; count: number }>(`/videos/${encodeURIComponent(String(identifier))}/analysis-jobs/history`, { token });
  },
  cancelAnalysisJob(token: string, identifier: string | number) {
    return request<AnalysisJobActionResult>(`/videos/${encodeURIComponent(String(identifier))}/analysis-jobs/cancel`, {
      token,
      method: "POST",
      body: {},
    });
  },
  retryAnalysisJob(token: string, identifier: string | number) {
    return request<AnalysisJobStartResult>(`/videos/${encodeURIComponent(String(identifier))}/analysis-jobs/retry`, {
      token,
      method: "POST",
      body: {},
    });
  },
  rerunAnalysisJob(token: string, identifier: string | number, options: AnalysisJobOptions) {
    return request<AnalysisJobStartResult>(`/videos/${encodeURIComponent(String(identifier))}/analysis-jobs/rerun`, {
      token,
      method: "POST",
      body: options,
    });
  },
  prepareVideoExport(token: string, identifier: string | number, kind: "video" | "frames", phase = "all", persist = true) {
    return request<VideoExportResult>(`/videos/${encodeURIComponent(String(identifier))}/exports`, {
      token,
      method: "POST",
      body: { kind, phase, persist },
    });
  },
  saveLatestVideoBundle(token: string) {
    return request<LatestVideoBundleResult>("/videos/latest-bundle", {
      token,
      method: "POST",
      body: {},
      timeoutMs: 300000,
    });
  },
  saveChartExport(
    token: string,
    identifier: string | number,
    payload: {
      phase: string;
      chart_name: string;
      filename: string;
      image_data: string;
      metrics?: Record<string, unknown>;
    },
  ) {
    return request<ChartExportResult>(`/videos/${encodeURIComponent(String(identifier))}/chart-exports`, {
      token,
      method: "POST",
      body: payload,
      timeoutMs: 120000,
    });
  },
  uploadVideo(token: string, file: File, exercise: string, patientUsername = "", fullName = "") {
    const body = new FormData();
    body.append("file", file);
    body.append("exercise", exercise);
    if (patientUsername) body.append("patient_username", patientUsername);
    if (fullName) body.append("full_name", fullName);
    return uploadRequest<VideoUploadResult>("/videos/upload", token, body);
  },
  createUser(
    token: string,
    payload: {
      username: string;
      email: string;
      full_name: string;
      password: string;
      password2: string;
      role: string;
      must_change_password: boolean;
    },
  ) {
    return request<{ ok: true; user: User }>("/admin/users", {
      token,
      method: "POST",
      body: payload,
    });
  },
  setUserActive(token: string, username: string, active: boolean) {
    return request<{ ok: true; user: User }>(`/admin/users/${encodeURIComponent(username)}/active`, {
      token,
      method: "PATCH",
      body: { active },
    });
  },
  createSymptom(
    token: string,
    payload: {
      vas: number;
      pain_location: string;
      exercise: string;
      symptoms: string;
      date: string;
    },
  ) {
    return request<{ ok: true; symptom: Record<string, unknown> }>("/symptoms", {
      token,
      method: "POST",
      body: payload,
    });
  },
  createSchedule(
    token: string,
    payload: {
      patient_username: string;
      title: string;
      date: string;
      time: string;
      note: string;
      kind?: string;
    },
  ) {
    return request<{ ok: true; schedule: Record<string, unknown> }>("/schedules", {
      token,
      method: "POST",
      body: payload,
    });
  },
  createEvaluation(
    token: string,
    identifier: string | number,
    payload: {
      doctor_result: string;
      comments: string;
      plan: string;
      errors: string | string[];
      comments_ncv?: string;
    },
  ) {
    return request<{ ok: true; evaluation: Record<string, unknown> }>(`/videos/${encodeURIComponent(String(identifier))}/evaluations`, {
      token,
      method: "POST",
      body: payload,
    });
  },
};
