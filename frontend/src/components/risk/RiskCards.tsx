"use client";

import { TwinZoneCard } from "@/services/api";

const FEATURE_LABELS: Record<string, string> = {
  density_norm: "Crowd density vs safe capacity",
  speed_drop: "Walking speed drop vs baseline",
  opposing_flow: "Opposing / conflicting movement",
  group_cohesion: "Dense group formation",
  abnormal_motion: "Abnormal motion / turbulence",
  exit_pressure: "Exit queue pressure",
  weather_factor: "Adverse weather impact",
  time_prior: "Event-phase congestion prior",
  historical_hotspot: "Historical hotspot pattern",
  emergency_flag: "Active emergency event",
  forecast_surge: "Predicted surge in next horizon",
};

export function RiskCards({ zones }: { zones: TwinZoneCard[] }) {
  const sorted = [...zones].sort((a, b) => b.risk.dcrs - a.risk.dcrs).slice(0, 3);
  return (
    <div className="panel panel-risk p-3">
      <h2 className="section-label mb-2 text-sm font-semibold text-ink">Explainable Risk</h2>
      <div className="space-y-2">
        {sorted.map((z) => {
          const contribs = (z.explanation.contributions || []).slice(0, 5);
          const maxImpact = Math.max(...contribs.map((c) => Math.abs(c.contribution)), 0.01);
          return (
            <details
              key={z.zone.id}
              className="rounded-lg border border-line bg-soft/40 p-3"
              open={z.risk.band === "red" || z.risk.band === "orange"}
            >
              <summary className="cursor-pointer list-none">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <div className="font-medium">
                      Zone {z.zone.code} — {z.zone.name}
                    </div>
                    <div className="font-mono text-xs text-mist">
                      {z.metrics.count} ppl · dens {z.metrics.density.toFixed(2)} · speed{" "}
                      {z.metrics.mean_speed.toFixed(2)}
                    </div>
                  </div>
                  <div
                    className={`rounded px-2 py-1 font-mono text-sm ${
                      z.risk.band === "red"
                        ? "bg-signal-red/20 text-signal-red"
                        : z.risk.band === "orange"
                          ? "bg-signal-orange/20 text-signal-orange"
                          : z.risk.band === "yellow"
                            ? "bg-signal-yellow/20 text-signal-yellow"
                            : "bg-signal-green/20 text-signal-green"
                    }`}
                  >
                    {z.risk.dcrs.toFixed(0)}
                  </div>
                </div>
              </summary>

              {contribs.length > 0 ? (
                <div className="mt-3 space-y-2 border-t border-line pt-2">
                  <div className="text-[11px] font-medium uppercase tracking-wide text-mist">
                    Why this score
                  </div>
                  {contribs.map((c) => {
                    const label = FEATURE_LABELS[c.feature] || c.feature;
                    const pct = Math.min(100, (Math.abs(c.contribution) / maxImpact) * 100);
                    return (
                      <div key={c.feature}>
                        <div className="mb-0.5 flex justify-between gap-2 font-mono text-[10px] text-ink/75">
                          <span className="truncate">{label}</span>
                          <span>
                            {c.value.toFixed(2)} · {c.contribution >= 0 ? "+" : ""}
                            {c.contribution.toFixed(2)}
                          </span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded bg-soft">
                          <div
                            className="h-full rounded bg-accent/80"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <pre className="mt-2 whitespace-pre-wrap font-mono text-[11px] text-ink/75">
                  {z.explanation.narrative}
                </pre>
              )}
            </details>
          );
        })}
        {!sorted.length && <p className="text-sm text-mist">No zone risk yet.</p>}
      </div>
    </div>
  );
}
