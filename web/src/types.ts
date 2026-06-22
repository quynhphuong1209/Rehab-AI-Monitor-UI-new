export type RoleKey = "admin" | "doctor_ktv" | "researcher" | "patient";

export type User = {
  username: string;
  full_name: string;
  email: string;
  role: string;
  role_key: RoleKey;
  active: boolean;
  must_change_password?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type LoginOptionUser = {
  username: string;
  full_name: string;
  role: string;
  role_key: RoleKey;
  active: boolean;
};

export type LoginOptionGroup = {
  role_key: RoleKey;
  role: string;
  count: number;
  users: LoginOptionUser[];
};

export type LoginOptionsPayload = {
  roles: LoginOptionGroup[];
};

export type Metrics = {
  accounts: number;
  patients: number;
  clinicians: number;
  researchers: number;
  admins: number;
  videos: number;
  videos_done: number;
  videos_processing: number;
  videos_pending: number;
  evaluations: number;
  symptoms: number;
  schedules: number;
  research_records: number;
  training_sessions: number;
};

export type DashboardPayload = {
  user: User;
  metrics: Metrics;
  source: {
    database_dir: string;
    users: string;
    video_list: string;
  };
  users: User[];
  videos: Record<string, unknown>[];
  latest_evaluated_videos: Record<string, unknown>[];
  evaluations: Record<string, unknown>[];
  symptoms: Record<string, unknown>[];
  schedules: Record<string, unknown>[];
  research_data: Record<string, unknown>[];
};

export type VideoDetailPayload = {
  id: number;
  video: Record<string, unknown>;
  media: {
    video_url: string;
    raw_video_url?: string;
    preview_image_url?: string;
    playback_status?: string;
    playback_codec?: string;
    file_exists: boolean;
    video_path: string;
    frame_data_exists: boolean;
    frame_preview_exists?: boolean;
    df_exists: boolean;
    analysis_artifact_exists?: boolean;
  };
  evaluations: Record<string, unknown>[];
  latest_evaluation: Record<string, unknown> | null;
  latest_job: AnalysisJob | null;
  frames: {
    index: number | string;
    timestamp?: string;
    status: string;
    phase?: string;
    phase_label?: string;
    phase_status?: string;
    threshold?: number | null;
    angle?: number | string | null;
    elbow?: number | string | null;
    left_shoulder?: number | string | null;
    left_elbow?: number | string | null;
    right_shoulder?: number | string | null;
    right_elbow?: number | string | null;
    shoulder_ref?: number | string | null;
    elbow_ref?: number | string | null;
    left_shoulder_ref?: number | string | null;
    left_elbow_ref?: number | string | null;
    right_shoulder_ref?: number | string | null;
    right_elbow_ref?: number | string | null;
    shoulder_delta?: number | string | null;
    elbow_delta?: number | string | null;
    ml_label?: string;
    ml_confidence?: number | string | null;
    ml_prob_pass?: number | string | null;
    ml_prob_near?: number | string | null;
    ml_prob_fail?: number | string | null;
    image_url: string;
    source?: string;
    exercise_key?: string;
    filtered_stranger?: boolean;
    stranger_reason?: string;
    ref_source?: string;
    youtube_ref_exercise_id?: number | string | null;
    motion_type?: string;
    youtube_ref_time?: number | string | null;
  }[];
  frame_groups?: {
    key: string;
    label: string;
    threshold?: number | null;
    total: number;
    start_offset?: number;
    end_offset?: number;
    pass: number;
    near: number;
    fail: number;
    unknown?: number;
  }[];
  frame_total: number;
  frame_offset?: number;
  frame_limit?: number;
  frame_phase?: string;
  frame_status?: string;
  chart: {
    points: { x: number; y: number }[];
    series?: {
      shoulder?: { x: number; y: number }[];
      elbow?: { x: number; y: number }[];
      shoulder_ref?: { x: number; y: number }[];
      elbow_ref?: { x: number; y: number }[];
    };
    histograms?: {
      shoulder?: { x0: number; x1: number; count: number }[];
      elbow?: { x0: number; x1: number; count: number }[];
    };
    boxplots?: {
      shoulder?: BoxPlotItem[];
      elbow?: BoxPlotItem[];
    };
    phase_boxplots?: {
      key: string;
      label: string;
      threshold?: number | null;
      shoulder?: BoxPlotItem[];
      elbow?: BoxPlotItem[];
    }[];
    pie?: { label: string; value: number }[];
    phase_pies?: {
      key: string;
      label: string;
      threshold?: number | null;
      total: number;
      pass: number;
      near: number;
      fail: number;
      unknown?: number;
      accuracy: number;
      pie: { label: string; value: number }[];
    }[];
    phase_metrics?: {
      key: string;
      label: string;
      threshold?: number | null;
      metrics: Record<string, number | string>;
    }[];
    radar?: {
      labels: string[];
      values: number[];
      targets: number[];
    };
    research_metrics?: Record<string, number | string>;
    phases?: { label: string; value: number }[];
    phase_ranges?: {
      key: string;
      label: string;
      threshold?: number | null;
      start: number;
      end: number;
    }[];
    source: string;
    row_count?: number;
  };
};

export type BoxPlotItem = {
  label: string;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  mean?: number;
  count?: number;
};

export type AnalysisJob = {
  job_id: string;
  run_id?: string;
  status: string;
  progress: number;
  status_msg?: string;
  error_msg?: string;
  updated_at?: string;
  heartbeat?: number | string;
  current_frame?: number | string | null;
  total_frames?: number | string | null;
  processed_frames?: number | string | null;
  elapsed_seconds?: number | string | null;
  fps_effective?: number | string | null;
  job_meta?: {
    action?: string;
    options?: AnalysisJobOptions;
    requested_by?: string;
  };
  steps?: { key: string; label: string; status: string }[];
};

export type AnalysisJobOptions = {
  model_type: string;
  skip_step: number;
  resize_width: number;
  min_confidence: number;
};

export type AnalysisJobStartResult = {
  started: boolean;
  reason: string;
  job: AnalysisJob;
};

export type AnalysisJobActionResult = {
  ok?: boolean;
  reason?: string;
  job: AnalysisJob | null;
};

export type VideoExportResult = {
  ok: boolean;
  kind: "video" | "frames" | string;
  phase: string;
  url: string;
  path: string;
  dataset_path?: string;
  dataset_manifest?: string;
  dataset_extra?: Record<string, unknown>;
  filename: string;
  size: number;
  updated_video?: Record<string, unknown>;
};

export type ChartExportResult = {
  ok: boolean;
  kind: "charts";
  phase: string;
  url: string;
  path: string;
  dataset_path?: string;
  dataset_manifest?: string;
  filename: string;
  size: number;
};

export type VideoUploadResult = {
  ok: boolean;
  video: Record<string, unknown>;
  size: number;
};

export type LatestVideoBundleResult = {
  ok: boolean;
  path: string;
  bundle: Record<string, unknown>;
};

export type AuthResponse = {
  token: string;
  user: User;
};

export type ApiErrorBody = {
  detail?: string;
};
