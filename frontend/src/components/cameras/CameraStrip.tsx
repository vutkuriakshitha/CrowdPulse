"use client";

import { Camera } from "@/services/api";

export function CameraStrip({ cameras }: { cameras: Camera[] }) {
  if (!cameras.length) {
    return (
      <div className="panel p-3 text-sm text-mist">
        No cameras registered for this venue yet.
      </div>
    );
  }

  return (
    <div className="panel panel-teal p-3">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="section-label text-sm font-semibold text-ink">Camera Network</h2>
        <span className="font-mono text-xs text-mist">{cameras.length} feeds · ingest via CCTV upload</span>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        {cameras.map((cam) => (
          <div
            key={cam.id}
            className="rounded-lg border border-line bg-soft/50 p-3 transition hover:border-accent/50"
          >
            <div className="flex items-center justify-between">
              <div className="font-medium">{cam.code}</div>
              <span
                className={`rounded px-1.5 py-0.5 font-mono text-[10px] ${
                  cam.is_active
                    ? "bg-signal-green/15 text-signal-green"
                    : "bg-signal-red/15 text-signal-red"
                }`}
              >
                {cam.is_active ? "ACTIVE" : "OFF"}
              </span>
            </div>
            <div className="mt-1 font-mono text-[11px] text-mist">
              {cam.edge_node_id} · {cam.fps} fps
            </div>
            <div className="mt-2 truncate font-mono text-[10px] text-mist">{cam.stream_url}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
