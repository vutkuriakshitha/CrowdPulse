"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  DetectionResult,
  fetchDetectorStatus,
  fetchVideos,
  getApiBase,
  processVideo,
  runPipeline,
  TwinSnapshot,
  uploadVideo,
  VideoAsset,
} from "@/services/api";
import { getToken } from "@/services/auth";

const MAX_UPLOAD_BYTES = 500 * 1024 * 1024;

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

type Phase = "idle" | "upload" | "analyze" | "detect" | "pipeline";

export function VideoUploadPanel({
  onTwinInvalidate,
  onDetectionReady,
}: {
  onTwinInvalidate?: (hint?: TwinSnapshot | null) => void | Promise<void>;
  onDetectionReady?: (info: {
    videoId: string;
    annotatedUrl: string;
    previewUrl?: string | null;
    maxCount?: number | null;
    uniqueTracks?: number | null;
    filename?: string | null;
  }) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [videos, setVideos] = useState<VideoAsset[]>([]);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [engine, setEngine] = useState<string>("");
  const [lastResult, setLastResult] = useState<DetectionResult | null>(null);
  const [progressPulse, setProgressPulse] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const [rows, det] = await Promise.all([fetchVideos(), fetchDetectorStatus()]);
      setVideos(rows);
      setEngine(`${det.backend}/${det.engine}`);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    if (!busy) {
      setProgressPulse(0);
      return;
    }
    const id = window.setInterval(() => setProgressPulse((p) => (p + 8) % 100), 280);
    return () => window.clearInterval(id);
  }, [busy]);

  const onAnalyzeCctv = async () => {
    if (!file) {
      setError("Choose a CCTV video file first");
      return;
    }
    if (file.size <= 0) {
      setError("Selected file is empty");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setError(`File too large (max ${formatBytes(MAX_UPLOAD_BYTES)})`);
      return;
    }
    setBusy(true);
    setPhase("analyze");
    setError(null);
    setWarning(null);
    try {
      setMessage(`Uploading ${file.name}…`);
      const saved = await uploadVideo(file, "control-room CCTV ingest");
      setFile(null);
      await refresh();
      setPhase("pipeline");
      setMessage("Analyzing full clip: detect → track → zones → DCRS → recommendations…");
      const result = await runPipeline({
        video_id: saved.id,
        use_latest_upload: false,
        include_twin: true,
      });
      setLastResult(result);
      if (result.annotated_url && result.video?.id) {
        onDetectionReady?.({
          videoId: result.video.id,
          annotatedUrl: result.annotated_url,
          previewUrl: result.preview_url,
          maxCount: result.summary?.max_count,
          uniqueTracks: result.summary?.unique_tracks,
          filename: result.video.original_filename,
        });
      }
      if (result.warning || result.empty_detections) {
        setWarning(result.warning || "No people detected in sampled frames.");
      }
      const stageNames = (result.stages || []).map((s) => String(s.name)).join(" → ");
      setMessage(
        `Ready in ${result.elapsed_ms}ms · peak ${result.peak_zone}:${result.peak_band} ` +
          `DCRS=${result.peak_dcrs?.toFixed?.(0) ?? result.peak_dcrs} · alerts=${result.alerts?.length ?? 0}` +
          (result.annotated_url ? " · annotated video ready" : "") +
          ` · ${stageNames}`,
      );
      await refresh();
      await onTwinInvalidate?.(result.twin || null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "CCTV analysis failed");
      setMessage(null);
    } finally {
      setBusy(false);
      setPhase("idle");
    }
  };

  const onProcess = async (id: string) => {
    setBusy(true);
    setPhase("detect");
    setError(null);
    setWarning(null);
    setMessage("Detecting people · tracking · zone analytics · DCRS…");
    try {
      const result = await processVideo(id);
      setLastResult(result);
      if (result.annotated_url && result.video?.id) {
        onDetectionReady?.({
          videoId: result.video.id,
          annotatedUrl: result.annotated_url,
          previewUrl: result.preview_url,
          maxCount: result.summary?.max_count,
          uniqueTracks: result.summary?.unique_tracks,
          filename: result.video.original_filename,
        });
      }
      if (result.warning || result.empty_detections) {
        setWarning(result.warning || "No people detected in sampled frames.");
      }
      const zones = result.zone_summary || result.summary.zone_summary || {};
      const zoneTxt = Object.entries(zones)
        .map(([code, z]) => `${code}:${z.latest_count}`)
        .join(" ");
      const peak =
        result.peak_zone && result.peak_band
          ? ` · peak ${result.peak_zone}:${result.peak_band} DCRS=${result.peak_dcrs?.toFixed?.(0) ?? result.peak_dcrs}`
          : "";
      setMessage(
        `Done (${result.backend}/${result.engine}` +
          `${result.tracker ? "+" + result.tracker : ""}) · tracks=${result.summary.unique_tracks ?? "-"} · max=${result.summary.max_count} · zones[${zoneTxt}]${peak}`,
      );
      await refresh();
      await onTwinInvalidate?.(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Detection failed");
      setMessage(null);
    } finally {
      setBusy(false);
      setPhase("idle");
    }
  };

  const onOneClickPipeline = async (sampleFilename?: string) => {
    setBusy(true);
    setPhase("pipeline");
    setError(null);
    setWarning(null);
    // If user picked a local file, upload it first so pipeline uses *that* clip
    let uploadedId: string | undefined;
    try {
      if (!sampleFilename && file) {
        setMessage(`Uploading ${file.name} then running detection pipeline…`);
        const saved = await uploadVideo(file);
        uploadedId = saved.id;
        setFile(null);
        await refresh();
      }
      setMessage(
        sampleFilename
          ? `Pipeline on sample ${sampleFilename}…`
          : uploadedId
            ? "Detecting people (boxes + IDs) → analytics → DCRS → twin…"
            : "Pipeline: resolve → detect → analytics → DCRS → explain → recommend → twin…",
      );
      const result = await runPipeline(
        sampleFilename
          ? {
              sample_filename: sampleFilename,
              use_latest_upload: false,
              include_twin: true,
            }
          : uploadedId
            ? {
                video_id: uploadedId,
                use_latest_upload: false,
                include_twin: true,
              }
            : {
                use_latest_upload: videos.length > 0,
                include_twin: true,
              },
      );
      setLastResult(result);
      if (result.annotated_url && result.video?.id) {
        onDetectionReady?.({
          videoId: result.video.id,
          annotatedUrl: result.annotated_url,
          previewUrl: result.preview_url,
          maxCount: result.summary?.max_count,
          uniqueTracks: result.summary?.unique_tracks,
          filename: result.video.original_filename,
        });
      }
      if (result.warning || result.empty_detections) {
        setWarning(result.warning || "No people detected in sampled frames.");
      }
      const stageNames = (result.stages || []).map((s) => String(s.name)).join(" → ");
      setMessage(
        `Pipeline OK in ${result.elapsed_ms}ms · peak ${result.peak_zone}:${result.peak_band} ` +
          `DCRS=${result.peak_dcrs?.toFixed?.(0) ?? result.peak_dcrs} · alerts=${result.alerts?.length ?? 0}` +
          (result.annotated_url ? " · annotated video ready" : "") +
          ` · ${stageNames}`,
      );
      await refresh();
      await onTwinInvalidate?.(result.twin || null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Pipeline failed");
      setMessage(null);
    } finally {
      setBusy(false);
      setPhase("idle");
    }
  };

  const phaseLabel =
    phase === "upload"
      ? "Uploading"
      : phase === "analyze"
        ? "Uploading & analyzing CCTV"
        : phase === "detect"
          ? "Processing video"
          : phase === "pipeline"
            ? "Running detection pipeline"
            : "";

  return (
    <div className="panel panel-teal p-3">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="section-label text-sm font-semibold text-ink">CCTV Video Ingest</h2>
        <span className="font-mono text-[10px] text-mist">{engine || "detector…"}</span>
      </div>

      <div className="rounded-lg border border-dashed border-line bg-soft/40 p-3">
        <label className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-mist">
          Upload a real CCTV clip (MP4 / MOV / AVI / MKV / WEBM, max {formatBytes(MAX_UPLOAD_BYTES)})
        </label>
        <input
          type="file"
          accept="video/*,.mp4,.avi,.mov,.mkv,.webm,.mpeg,.mpg,.m4v,.ts"
          disabled={busy}
          onClick={(e) => {
            // Allow selecting the same file again
            (e.target as HTMLInputElement).value = "";
          }}
          onChange={(e) => {
            const f = e.target.files?.[0] || null;
            setError(null);
            setWarning(null);
            if (!f) {
              setFile(null);
              return;
            }
            const name = f.name.toLowerCase();
            const okExt = /\.(mp4|avi|mov|mkv|webm|mpeg|mpg|m4v|ts)$/i.test(name);
            if (!okExt && !f.type.startsWith("video/")) {
              setFile(null);
              setError("Unsupported file. Use MP4, MOV, AVI, MKV, or WEBM.");
              return;
            }
            if (f.size <= 0) {
              setFile(null);
              setError("Selected file is empty");
              return;
            }
            if (f.size > MAX_UPLOAD_BYTES) {
              setFile(null);
              setError(`File too large (max ${formatBytes(MAX_UPLOAD_BYTES)})`);
              return;
            }
            setFile(f);
            setMessage(`Selected ${f.name} (${formatBytes(f.size)}) — click Analyze CCTV`);
          }}
          className="block w-full cursor-pointer text-sm text-mist file:mr-3 file:cursor-pointer file:rounded file:border-0 file:bg-accent file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white"
        />
        {file && (
          <p className="mt-2 rounded border border-accent/30 bg-accent/10 px-2 py-1 font-mono text-xs text-accent">
            Ready: {file.name} · {formatBytes(file.size)}
          </p>
        )}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onAnalyzeCctv}
            disabled={busy || !file}
            className="rounded bg-accent px-3 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
          >
            {phase === "analyze" || phase === "pipeline" ? "Analyzing…" : "Analyze CCTV"}
          </button>
          <button
            type="button"
            onClick={() => onOneClickPipeline()}
            disabled={busy}
            className="rounded border border-accent px-3 py-2 text-sm font-medium text-accent hover:bg-accent/10 disabled:opacity-50"
          >
            {phase === "pipeline" && !file ? "Running pipeline…" : "Re-run latest / samples"}
          </button>
          {file && (
            <span className="font-mono text-xs text-mist">
              {file.name} · {formatBytes(file.size)}
            </span>
          )}
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {(
            [
              ["sparse_crowd.mp4", "Sparse"],
              ["medium_crowd.mp4", "Medium"],
              ["dense_crowd.mp4", "Dense"],
              ["real_world_crowd.mp4", "Real CCTV"],
            ] as const
          ).map(([fname, label]) => (
            <button
              key={fname}
              type="button"
              disabled={busy}
              onClick={() => onOneClickPipeline(fname)}
              className="rounded border border-line px-2 py-0.5 font-mono text-[10px] text-mist hover:border-accent/50 hover:text-ink disabled:opacity-50"
            >
              Sample: {label}
            </button>
          ))}
        </div>
        <p className="mt-2 font-mono text-[10px] text-mist">
          Real CCTV: choose a file then <span className="text-ink/75">Analyze CCTV</span>. The
          pipeline samples frames across the whole clip (not only the first seconds), then updates
          the twin, risk, and recommendations. Dense sample = highest synthetic risk for rehearsal.
        </p>
      </div>

      {busy && (
        <div className="mt-2 rounded border border-accent/30 bg-accent/10 px-2 py-2">
          <div className="mb-1 flex items-center justify-between font-mono text-[10px] text-accent">
            <span className="inline-flex items-center gap-2">
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-accent" />
              {phaseLabel}
            </span>
            <span>please wait</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded bg-soft">
            <div
              className="h-full rounded bg-accent/80 transition-all duration-300"
              style={{ width: `${20 + progressPulse * 0.7}%` }}
            />
          </div>
        </div>
      )}

      {message && (
        <p className="mt-2 rounded border border-signal-green/30 bg-signal-green/10 px-2 py-1.5 text-xs text-signal-green">
          {message}
        </p>
      )}
      {warning && (
        <p className="mt-2 rounded border border-signal-orange/40 bg-signal-orange/10 px-2 py-1.5 text-xs text-signal-orange">
          {warning}
        </p>
      )}
      {error && (
        <p className="mt-2 rounded border border-signal-red/30 bg-signal-red/10 px-2 py-1.5 text-xs text-signal-red">
          {error}
        </p>
      )}

      {lastResult && (
        <div className="mt-3 rounded-lg border border-line bg-soft/50 p-2">
          <div className="mb-1 text-xs font-medium text-mist">
            Zone analytics + DCRS
            {lastResult.peak_band
              ? ` · peak ${lastResult.peak_zone}:${String(lastResult.peak_band).toUpperCase()} (${lastResult.peak_dcrs?.toFixed?.(0)})`
              : ""}
          </div>

          {(lastResult.annotated_url || lastResult.preview_url) && (
            <div className="mb-3 overflow-hidden rounded-lg border border-accent/40 bg-ink/5">
              <div className="flex items-center justify-between border-b border-line bg-accent/10 px-2 py-1.5">
                <span className="font-mono text-[11px] font-semibold text-accent">
                  Detection proof · numbered persons
                </span>
                <span className="font-mono text-[10px] text-mist">
                  max {lastResult.summary?.max_count ?? "—"} · tracks{" "}
                  {lastResult.summary?.unique_tracks ?? "—"}
                </span>
              </div>
              {lastResult.annotated_url ? (
                <video
                  key={lastResult.annotated_url}
                  className="max-h-[360px] w-full bg-black object-contain"
                  controls
                  autoPlay
                  muted
                  playsInline
                  poster={
                    lastResult.preview_url
                      ? `${getApiBase()}${lastResult.preview_url}?token=${encodeURIComponent(getToken() || "")}`
                      : undefined
                  }
                  src={`${getApiBase()}${lastResult.annotated_url}?token=${encodeURIComponent(getToken() || "")}`}
                />
              ) : lastResult.preview_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`${getApiBase()}${lastResult.preview_url}?token=${encodeURIComponent(getToken() || "")}`}
                  alt="Annotated detection preview"
                  className="max-h-[360px] w-full object-contain"
                />
              ) : null}
              <p className="px-2 py-1.5 font-mono text-[10px] text-mist">
                Green box + #ID on each person. Banner shows live people-in-frame count.
              </p>
            </div>
          )}

          <div className="mb-2 grid grid-cols-2 gap-1 sm:grid-cols-4">
            {Object.entries(lastResult.zone_summary || lastResult.summary.zone_summary || {}).map(
              ([code, z]) => {
                const risk = lastResult.risk_by_zone?.[code];
                const band = risk?.band ? String(risk.band) : "";
                const bandCls =
                  band === "red"
                    ? "border-signal-red/50 text-signal-red"
                    : band === "orange"
                      ? "border-amber-500/50 text-amber-400"
                      : band === "yellow"
                        ? "border-yellow-500/40 text-yellow-300"
                        : "border-line text-mist";
                return (
                  <div key={code} className={`rounded border bg-soft/60 px-2 py-1 ${bandCls}`}>
                    <div className="font-mono text-[10px] opacity-80">Zone {code}</div>
                    <div className="text-sm font-semibold text-ink">
                      {z.latest_count} ppl
                      {risk ? ` · ${risk.dcrs.toFixed(0)} ${band.toUpperCase()}` : ""}
                    </div>
                    <div className="font-mono text-[10px] text-mist">
                      dens {z.density.toFixed(2)} · spd {(z.mean_speed ?? 0).toFixed(2)}
                    </div>
                  </div>
                );
              },
            )}
          </div>
          <div className="mb-1 text-xs font-medium text-mist">Count timeline</div>
          <div className="max-h-28 overflow-auto font-mono text-[10px] text-ink/75">
            {(lastResult.timeline || []).slice(0, 20).map((p) => (
              <div key={p.frame_index}>
                t={p.time_sec.toFixed(1)}s · tracks={p.count}
                {p.zone_counts
                  ? ` · ${Object.entries(p.zone_counts)
                      .map(([k, v]) => `${k}:${v}`)
                      .join(" ")}`
                  : ""}
              </div>
            ))}
            {!lastResult.timeline?.length && (
              <div className="text-signal-orange">No timeline frames (empty or unreadable video).</div>
            )}
          </div>
        </div>
      )}

      <div className="mt-3 space-y-2">
        <div className="text-xs font-medium text-mist">Recent uploads</div>
        {!videos.length && <p className="text-xs text-mist">No videos uploaded yet.</p>}
        {videos.slice(0, 5).map((v) => (
          <div
            key={v.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-soft/50 px-3 py-2"
          >
            <div>
              <div className="text-sm">{v.original_filename}</div>
              <div className="font-mono text-[11px] text-mist">
                {formatBytes(v.size_bytes)} · {v.source} · {v.status}
              </div>
            </div>
            <button
              type="button"
              onClick={() => onProcess(v.id)}
              disabled={busy || v.status === "processing"}
              className="rounded border border-line px-2 py-1 text-xs hover:border-accent disabled:opacity-50"
            >
              {v.status === "processing" || (busy && phase === "detect")
                ? "Processing…"
                : "Process Video"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
