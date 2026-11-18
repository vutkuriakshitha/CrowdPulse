import { clearSession, getToken } from "@/services/auth";

export type RiskBand = "green" | "yellow" | "orange" | "red";

export type RiskContribution = {
  feature: string;
  label?: string;
  value: number;
  weight?: number;
  contribution: number;
};

export type RiskExplanationPayload = {
  narrative: string;
  contributions?: RiskContribution[];
  top_labels?: string[];
};

export type TwinZoneCard = {
  zone: {
    id: string;
    code: string;
    name: string;
    polygon: number[][];
    exits: string[];
    area_m2?: number;
    capacity?: number;
  };
  metrics: {
    count: number;
    density: number;
    mean_speed: number;
    opposing_flow: number;
  };
  risk: {
    dcrs: number;
    band: RiskBand;
  };
  explanation: RiskExplanationPayload;
  forecast_density: Record<string, number>;
};

export type ActionStatus = "pending" | "accepted" | "dismissed" | "executed";

export type TwinAction = {
  action_type: string;
  title: string;
  priority?: number;
  confidence?: number;
  status?: ActionStatus | string;
  acked_by?: string;
  acked_by_name?: string;
  acked_at?: number;
};

export type TwinAlert = {
  id: string;
  zone_code: string;
  dcrs: number;
  band?: string;
  explanation: string | RiskExplanationPayload;
  actions: TwinAction[];
  rationale: string;
  queue_status?: string;
};

export type TwinSnapshot = {
  venue: { id?: string; name: string; timezone?: string; cameras?: Camera[] };
  zones: TwinZoneCard[];
  alerts: TwinAlert[];
  generated_at?: number;
  peak_dcrs?: number;
  peak_zone?: string;
  peak_band?: string;
};

export type Camera = {
  id: string;
  code: string;
  stream_url: string;
  fps: number;
  edge_node_id: string;
  is_active: boolean;
};

export type Venue = {
  id: string;
  name: string;
  timezone: string;
  zones: Array<{
    id: string;
    code: string;
    name: string;
    area_m2: number;
    capacity: number;
    exits: string[];
  }>;
  cameras: Camera[];
};

export type HealthStatus = {
  status: string;
  service: string;
  version: string;
  database?: { ok: boolean; venues: number };
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function apiUnreachableMessage(): string {
  return `Cannot reach CrowdPulse API at ${API}. Is the backend running?`;
}

function authHeaders(init?: HeadersInit): HeadersInit {
  const token = getToken();
  const base: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) base.Authorization = `Bearer ${token}`;
  return { ...base, ...(init || {}) };
}

function handleUnauthorized(status: number): void {
  if (status === 401 && typeof window !== "undefined") {
    clearSession();
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
  }
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = 60_000): Promise<T> {
  let res: Response;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    res = await fetch(`${API}${path}`, {
      ...init,
      signal: controller.signal,
      cache: "no-store",
      headers: authHeaders(init?.headers),
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(`Request timed out talking to ${API}`);
    }
    throw new ApiError(apiUnreachableMessage());
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    handleUnauthorized(res.status);
    let detail = `API ${path} failed`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export function getApiBase(): string {
  return API;
}

export async function fetchHealth(): Promise<HealthStatus> {
  // Health stays public (no auth header required, but sending token is fine)
  let res: Response;
  try {
    res = await fetch(`${API}/health`, { cache: "no-store" });
  } catch {
    throw new ApiError(apiUnreachableMessage());
  }
  if (!res.ok) throw new ApiError("API /health failed", res.status);
  return res.json();
}

export async function fetchDemoVenue(): Promise<Venue> {
  return request<Venue>("/api/v1/venues/demo");
}

export async function fetchTwinSnapshot(): Promise<TwinSnapshot> {
  return request<TwinSnapshot>("/api/v1/twin/snapshot");
}

export type WhatIfZoneRisk = {
  zone_code: string;
  dcrs: number;
  band?: string;
  density?: number;
  exit_pressure?: number;
  forecast_density?: number;
  exits_effective?: string[];
};

export type WhatIfResult = {
  narrative: string;
  predicted_peak_dcrs: number;
  baseline_peak_dcrs?: number;
  dcrs_delta?: number;
  congested_zones?: string[];
  zone_risks?: WhatIfZoneRisk[];
  recommended_actions?: TwinAction[];
  simulation_id?: string;
  persisted?: boolean;
};

export async function runWhatIf(body: {
  name: string;
  close_exits?: string[];
  rainfall_mm_h?: number;
  vip_zone?: string | null;
  hold_ingress?: boolean;
  horizon_minutes?: number;
}): Promise<WhatIfResult> {
  return request<WhatIfResult>("/api/v1/simulation/what-if", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type IncidentReportResult = {
  id?: string | null;
  markdown: string;
  format?: string;
  source?: "ollama" | "template" | string;
  persisted?: boolean;
  generated_at?: number;
  context?: {
    event_name?: string;
    venue_name?: string;
    peak_dcrs?: number;
    peak_zone?: string;
    peak_band?: string;
    hotspot_zones?: string[];
  };
};

export async function generateReport(body?: {
  event_name?: string;
  venue_name?: string;
  use_live_twin?: boolean;
}): Promise<IncidentReportResult> {
  return request<IncidentReportResult>("/api/v1/reports/incident", {
    method: "POST",
    body: JSON.stringify({ use_live_twin: true, ...(body || {}) }),
  });
}

export type HotspotRow = {
  rank: number;
  zone_code: string;
  zone_name: string;
  historical_score: number;
  rank_score: number;
  current_density: number;
  current_dcrs: number;
  band: string;
  mean_speed?: number;
  opposing_flow?: number;
  exit_pressure?: number;
  recommendation: string;
};

export type TrendPoint = {
  t: number;
  density: number;
  dcrs: number;
  count?: number;
  band?: string;
};

export type TrendResponse = {
  source: string;
  zone_code: string;
  points: TrendPoint[];
  run_id?: string;
  series?: Record<string, string>;
  hint?: string;
};

export async function fetchHotspots() {
  return request<{ hotspots: HotspotRow[]; count: number }>("/api/v1/analytics/hotspots");
}

export async function fetchTrends(zone?: string) {
  const q = zone ? `?zone=${encodeURIComponent(zone)}` : "";
  return request<TrendResponse>(`/api/v1/analytics/trends${q}`);
}

export type VideoAsset = {
  id: string;
  venue_id?: string | null;
  original_filename: string;
  stored_filename: string;
  content_type: string;
  size_bytes: number;
  source: string;
  status: string;
  notes?: string | null;
  created_at?: string | null;
};

export async function fetchVideos(): Promise<VideoAsset[]> {
  return request<VideoAsset[]>("/api/v1/videos/");
}

export async function uploadVideo(file: File, notes?: string): Promise<VideoAsset> {
  const form = new FormData();
  form.append("file", file);
  if (notes) form.append("notes", notes);

  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20 * 60 * 1000);
  let res: Response;
  try {
    res = await fetch(`${API}/api/v1/videos/upload`, {
      method: "POST",
      body: form,
      headers,
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("Upload timed out. Try a shorter clip or a smaller MP4.");
    }
    throw new ApiError(apiUnreachableMessage());
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    handleUnauthorized(res.status);
    let detail = `Upload failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

export async function queueVideo(videoId: string): Promise<VideoAsset> {
  return request<VideoAsset>(`/api/v1/videos/${videoId}/queue`, { method: "POST" });
}

export type DetectionResult = {
  ok?: boolean;
  video: { id: string; status: string; original_filename: string };
  run_id: string;
  engine: string;
  backend: string;
  tracker?: string;
  empty_detections?: boolean;
  warning?: string | null;
  summary: {
    max_count: number;
    avg_count: number;
    frames_processed: number;
    fps: number;
    duration_sec: number;
    unique_tracks?: number;
    zone_summary?: Record<
      string,
      {
        zone_id: string;
        name: string;
        latest_count: number;
        max_count: number;
        avg_count: number;
        density: number;
      }
    >;
  };
  zone_summary?: Record<
    string,
    {
      zone_id: string;
      name: string;
      latest_count: number;
      max_count: number;
      avg_count: number;
      density: number;
      mean_speed?: number;
      opposing_flow?: number;
      congestion_index?: number;
      abnormal_motion?: number;
      exit_pressure?: number;
    }
  >;
  zone_analytics?: Record<string, Record<string, number>>;
  risk_by_zone?: Record<
    string,
    {
      zone_id: string;
      dcrs: number;
      band: RiskBand | string;
      count?: number;
      density?: number;
      mean_speed?: number;
      opposing_flow?: number;
      exit_pressure?: number;
      explanation?: string;
    }
  >;
  peak_dcrs?: number;
  peak_zone?: string;
  peak_band?: RiskBand | string;
  annotated_url?: string | null;
  preview_url?: string | null;
  alerts?: Array<{
    id: string;
    zone_code: string;
    dcrs: number;
    band: string;
    explanation?: string;
  }>;
  timeline: Array<{
    frame_index: number;
    time_sec: number;
    count: number;
    avg_confidence: number;
    zone_counts?: Record<string, number>;
    active_tracks?: number;
    mean_speed?: number;
    opposing_flow?: number;
  }>;
};

export async function processVideo(videoId: string): Promise<DetectionResult> {
  return request<DetectionResult>(`/api/v1/videos/${videoId}/process`, { method: "POST" }, 20 * 60 * 1000);
}

export type PipelineResult = DetectionResult & {
  ok: boolean;
  pipeline: string;
  stages: Array<Record<string, unknown>>;
  elapsed_ms: number;
  flow: string[];
  twin?: TwinSnapshot;
};

export async function runPipeline(body?: {
  video_id?: string;
  sample_filename?: string;
  use_latest_upload?: boolean;
  frame_stride?: number;
  max_frames?: number;
  include_twin?: boolean;
}): Promise<PipelineResult> {
  return request<PipelineResult>("/api/v1/pipeline/run", {
    method: "POST",
    body: JSON.stringify(body || {}),
  }, 20 * 60 * 1000);
}

export async function fetchDetections(videoId: string): Promise<{
  video_id: string;
  run_id: string;
  engine: string;
  backend: string;
  status: string;
  summary?: Record<string, unknown> & {
    annotated_url?: string;
    preview_url?: string;
    max_count?: number;
    unique_tracks?: number;
  };
  annotated_url?: string | null;
  preview_url?: string | null;
  timeline?: unknown[];
}> {
  return request(`/api/v1/videos/${videoId}/detections`);
}

export async function fetchDetectorStatus() {
  return request<{ engine: string; backend: string }>("/api/v1/videos/detector/status");
}

export type AckResult = {
  ok: boolean;
  persisted?: boolean;
  action: TwinAction;
  alert: TwinAlert;
  operator?: { username: string; full_name: string; role: string };
};

export async function ackAction(body: {
  alert_id: string;
  action_type: string;
  status: "accepted" | "dismissed" | "executed";
}): Promise<AckResult> {
  return request<AckResult>("/api/v1/decisions/ack", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
