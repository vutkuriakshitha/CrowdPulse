"use client";

import { useEffect, useMemo, useState } from "react";
import { getApiBase } from "@/services/api";
import { getToken } from "@/services/auth";

type Props = {
  videoId?: string | null;
  annotatedUrl?: string | null;
  previewUrl?: string | null;
  maxCount?: number | null;
  uniqueTracks?: number | null;
  filename?: string | null;
};

/**
 * Prominent YOLO proof player: numbered boxes + people-in-frame banner.
 */
export function DetectionProofPlayer({
  videoId,
  annotatedUrl,
  previewUrl,
  maxCount,
  uniqueTracks,
  filename,
}: Props) {
  const token = typeof window !== "undefined" ? getToken() : null;
  const [failed, setFailed] = useState(false);
  const bust = "v=h264";

  const withAuth = (url: string | null | undefined) => {
    if (!url || !token) return null;
    const base = url.startsWith("http") ? url : `${getApiBase()}${url}`;
    const join = base.includes("?") ? "&" : "?";
    return `${base}${join}token=${encodeURIComponent(token)}&${bust}`;
  };

  const annSrc = useMemo(() => withAuth(annotatedUrl || null), [annotatedUrl, token]);
  const posterSrc = useMemo(() => withAuth(previewUrl || null), [previewUrl, token]);

  useEffect(() => {
    setFailed(false);
  }, [annSrc]);

  if (!annSrc && !posterSrc) {
    return (
      <div className="panel panel-teal p-4">
        <h2 className="section-label text-sm font-semibold text-ink">Detection Proof (YOLO)</h2>
        <p className="mt-2 text-sm text-mist">
          Run <span className="font-medium text-ink">One-Click Full Pipeline</span> on a CCTV clip
          (admin). An annotated video with green boxes and person <span className="font-mono">#ID</span>{" "}
          labels will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="panel panel-teal overflow-hidden p-0">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line bg-accent/10 px-3 py-2">
        <div>
          <h2 className="section-label text-sm font-semibold text-ink">Detection Proof (YOLO)</h2>
          <p className="mt-0.5 font-mono text-[10px] text-mist">
            {filename || "CCTV"} · green box + #ID per person · live people-in-frame banner
          </p>
        </div>
        <div className="font-mono text-[11px] text-accent">
          max {maxCount ?? "—"} ppl · {uniqueTracks ?? "—"} tracks
          {videoId ? ` · ${videoId.slice(0, 8)}…` : ""}
        </div>
      </div>

      {/* Always show still proof first so boxes are visible even if video codec fails */}
      {posterSrc && (
        <div className="border-b border-line bg-black">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={posterSrc}
            alt="Annotated frame with numbered persons"
            className="max-h-[320px] w-full object-contain"
          />
          <p className="bg-soft/90 px-3 py-1 font-mono text-[10px] text-mist">
            Still frame proof (boxes + IDs). Playable clip below.
          </p>
        </div>
      )}

      {annSrc && !failed ? (
        <video
          key={annSrc}
          className="max-h-[360px] w-full bg-black object-contain"
          controls
          autoPlay
          muted
          playsInline
          preload="auto"
          poster={posterSrc || undefined}
          src={annSrc}
          onError={() => setFailed(true)}
        >
          <source src={annSrc} type="video/mp4" />
        </video>
      ) : (
        !posterSrc && (
          <p className="p-4 text-sm text-signal-orange">Annotated media failed to load. Re-run pipeline.</p>
        )
      )}

      {failed && posterSrc && (
        <p className="border-t border-line px-3 py-2 text-xs text-signal-orange">
          Video codec blocked in browser — still frame above still shows numbered detections.
        </p>
      )}

      <p className="border-t border-line px-3 py-2 font-mono text-[10px] text-mist">
        Each person is boxed and numbered (#1, #2, …). Banner shows count in that frame.
      </p>
    </div>
  );
}
