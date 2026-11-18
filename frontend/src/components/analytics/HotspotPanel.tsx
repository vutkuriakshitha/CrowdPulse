"use client";

import { useEffect, useState } from "react";
import { fetchHotspots, HotspotRow } from "@/services/api";

function bandClass(band?: string): string {
  if (band === "red") return "text-signal-red";
  if (band === "orange") return "text-signal-orange";
  if (band === "yellow") return "text-signal-yellow";
  return "text-signal-green";
}

export function HotspotPanel() {
  const [rows, setRows] = useState<HotspotRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    const load = () => {
      fetchHotspots()
        .then((d) => {
          if (!alive) return;
          setRows(d.hotspots || []);
          setError(null);
        })
        .catch(() => {
          if (!alive) return;
          setError("Hotspots unavailable");
          setRows([]);
        })
        .finally(() => {
          if (alive) setLoading(false);
        });
    };
    load();
    const id = window.setInterval(load, 8000);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, []);

  return (
    <div className="flex max-h-[200px] flex-col overflow-hidden">
      <div className="mb-1.5 flex items-center justify-between">
        <h3 className="font-mono text-[10px] uppercase tracking-wider text-mist">Hotspot ranking</h3>
        <span className="font-mono text-[10px] text-mist">{loading ? "…" : `${rows.length} zones`}</span>
      </div>
      {error && <p className="mb-1 text-[11px] text-signal-orange">{error}</p>}
      <div className="min-h-0 flex-1 space-y-1 overflow-auto">
        {rows.map((r) => (
          <div
            key={r.zone_code}
            className="rounded border border-line/70 bg-soft/40 px-2 py-1.5"
            title={r.recommendation}
          >
            <div className="flex items-center justify-between gap-2 font-mono text-[11px]">
              <span className="text-ink/90">
                <span className="text-mist">#{r.rank}</span> {r.zone_code} · {r.zone_name}
              </span>
              <span className={bandClass(r.band)}>{(r.band || "").toUpperCase()}</span>
            </div>
            <div className="mt-0.5 flex justify-between font-mono text-[10px] text-mist">
              <span>hist {(r.historical_score * 100).toFixed(0)}%</span>
              <span>
                DCRS {r.current_dcrs.toFixed(0)} · dens {r.current_density.toFixed(1)}
              </span>
            </div>
          </div>
        ))}
        {!loading && !rows.length && !error && (
          <p className="text-xs text-mist">No hotspot data yet.</p>
        )}
      </div>
    </div>
  );
}
