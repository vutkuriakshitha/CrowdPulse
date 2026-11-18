"use client";

import { useMemo, useState } from "react";
import { ApiError, runWhatIf, WhatIfResult } from "@/services/api";

const EXIT_OPTIONS = ["", "Gate-A", "Gate-B", "Gate-C", "Gate-D", "Gate-E"];
const ZONE_OPTIONS = ["", "A", "B", "C", "D"];
const HORIZONS = [5, 10];

type Props = {
  exits?: string[];
  zoneCodes?: string[];
};

function bandClass(band?: string): string {
  if (band === "red") return "text-signal-red";
  if (band === "orange") return "text-signal-orange";
  if (band === "yellow") return "text-signal-yellow";
  return "text-signal-green";
}

export function WhatIfPanel({ exits, zoneCodes }: Props) {
  const exitChoices = useMemo(() => {
    const fromVenue = (exits || []).filter(Boolean);
    if (fromVenue.length) return ["", ...Array.from(new Set(fromVenue))];
    return EXIT_OPTIONS;
  }, [exits]);

  const zoneChoices = useMemo(() => {
    const fromVenue = (zoneCodes || []).filter(Boolean);
    if (fromVenue.length) return ["", ...fromVenue];
    return ZONE_OPTIONS;
  }, [zoneCodes]);

  const [closeExit, setCloseExit] = useState("Gate-C");
  const [rain, setRain] = useState(0);
  const [vip, setVip] = useState("");
  const [holdIngress, setHoldIngress] = useState(false);
  const [horizon, setHorizon] = useState(10);
  const [result, setResult] = useState<WhatIfResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onRun = async (preset?: "gate-c" | "rain" | "vip") => {
    let nextExit = closeExit;
    let nextRain = rain;
    let nextVip = vip;
    let nextHold = holdIngress;

    if (preset === "gate-c") {
      nextExit = "Gate-C";
      nextRain = 0;
      nextVip = "";
      nextHold = false;
      setCloseExit("Gate-C");
      setRain(0);
      setVip("");
      setHoldIngress(false);
    } else if (preset === "rain") {
      nextExit = "";
      nextRain = 20;
      nextVip = "";
      setCloseExit("");
      setRain(20);
      setVip("");
    } else if (preset === "vip") {
      nextExit = "";
      nextRain = 0;
      nextVip = "B";
      setCloseExit("");
      setRain(0);
      setVip("B");
    }

    setLoading(true);
    setError(null);
    try {
      const data = await runWhatIf({
        name:
          preset === "gate-c"
            ? "Close Gate-C"
            : preset === "rain"
              ? "Heavy rainfall"
              : preset === "vip"
                ? "VIP ingress Zone B"
                : "Ops what-if",
        close_exits: nextExit ? [nextExit] : [],
        rainfall_mm_h: nextRain,
        vip_zone: nextVip || null,
        hold_ingress: nextHold,
        horizon_minutes: horizon,
      });
      setResult(data);
    } catch (e) {
      setResult(null);
      setError(e instanceof ApiError ? e.message : "Simulation API unavailable");
    } finally {
      setLoading(false);
    }
  };

  const delta = result?.dcrs_delta;
  const rising = typeof delta === "number" && delta > 0.05;

  return (
    <div className="panel panel-amber flex h-full max-h-[520px] flex-col overflow-hidden p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="section-label text-sm font-semibold text-ink">What-If Simulation</h2>
        <span className="font-mono text-[10px] text-mist">{horizon} min forecast</span>
      </div>

      <div className="mb-2 flex flex-wrap gap-1.5">
        <button
          type="button"
          onClick={() => onRun("gate-c")}
          disabled={loading}
          className="rounded border border-line px-2 py-0.5 font-mono text-[10px] text-mist hover:border-accent/50 hover:text-ink disabled:opacity-50"
        >
          Demo: Close Gate-C
        </button>
        <button
          type="button"
          onClick={() => onRun("rain")}
          disabled={loading}
          className="rounded border border-line px-2 py-0.5 font-mono text-[10px] text-mist hover:border-accent/50 hover:text-ink disabled:opacity-50"
        >
          Rain 20mm
        </button>
        <button
          type="button"
          onClick={() => onRun("vip")}
          disabled={loading}
          className="rounded border border-line px-2 py-0.5 font-mono text-[10px] text-mist hover:border-accent/50 hover:text-ink disabled:opacity-50"
        >
          VIP Zone B
        </button>
      </div>

      <div className="space-y-2 text-sm">
        <label className="block">
          <span className="font-mono text-[10px] uppercase tracking-wider text-mist">Close exit</span>
          <select
            className="mt-1 w-full rounded border border-line bg-soft px-2 py-1.5 text-sm text-ink outline-none focus:border-accent"
            value={closeExit}
            onChange={(e) => setCloseExit(e.target.value)}
          >
            {exitChoices.map((e) => (
              <option key={e || "none"} value={e}>
                {e || "None — keep all exits open"}
              </option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-2 gap-2">
          <label className="block">
            <span className="font-mono text-[10px] uppercase tracking-wider text-mist">Rainfall mm/h</span>
            <input
              type="number"
              min={0}
              max={80}
              className="mt-1 w-full rounded border border-line bg-soft px-2 py-1.5 text-sm text-ink outline-none focus:border-accent"
              value={rain}
              onChange={(e) => setRain(Number(e.target.value))}
            />
          </label>
          <label className="block">
            <span className="font-mono text-[10px] uppercase tracking-wider text-mist">Horizon</span>
            <select
              className="mt-1 w-full rounded border border-line bg-soft px-2 py-1.5 text-sm text-ink outline-none focus:border-accent"
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
            >
              {HORIZONS.map((h) => (
                <option key={h} value={h}>
                  {h} minutes
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="block">
          <span className="font-mono text-[10px] uppercase tracking-wider text-mist">VIP zone</span>
          <select
            className="mt-1 w-full rounded border border-line bg-soft px-2 py-1.5 text-sm text-ink outline-none focus:border-accent"
            value={vip}
            onChange={(e) => setVip(e.target.value)}
          >
            {zoneChoices.map((z) => (
              <option key={z || "none"} value={z}>
                {z ? `Zone ${z}` : "None"}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-xs text-mist">
          <input
            type="checkbox"
            checked={holdIngress}
            onChange={(e) => setHoldIngress(e.target.checked)}
            className="rounded border-line"
          />
          Hold ingress at entry zones
        </label>

        <button
          type="button"
          onClick={() => onRun()}
          disabled={loading}
          className="w-full rounded bg-accent px-3 py-2 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-60"
        >
          {loading ? "Simulating…" : `Predict next ${horizon} minutes`}
        </button>
      </div>

      {error && (
        <p className="mt-2 rounded border border-signal-red/40 bg-signal-red/10 px-2 py-1.5 text-xs text-signal-red">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-3 min-h-0 flex-1 space-y-2 overflow-auto border-t border-line pt-3">
          <p className="text-xs leading-relaxed text-ink/75">{result.narrative}</p>

          <div className="grid grid-cols-3 gap-2 font-mono text-[11px]">
            <div className="rounded border border-line bg-soft/50 px-2 py-1.5">
              <div className="text-mist">Peak</div>
              <div className="text-lg text-ink">{result.predicted_peak_dcrs.toFixed(1)}</div>
            </div>
            <div className="rounded border border-line bg-soft/50 px-2 py-1.5">
              <div className="text-mist">Baseline</div>
              <div className="text-lg text-ink">
                {(result.baseline_peak_dcrs ?? 0).toFixed(1)}
              </div>
            </div>
            <div className="rounded border border-line bg-soft/50 px-2 py-1.5">
              <div className="text-mist">Delta</div>
              <div className={`text-lg ${rising ? "text-signal-orange" : "text-signal-green"}`}>
                {typeof delta === "number" ? `${delta > 0 ? "+" : ""}${delta.toFixed(1)}` : "—"}
              </div>
            </div>
          </div>

          <div className="font-mono text-[11px] text-mist">
            Congested:{" "}
            <span className="text-ink/90">
              {(result.congested_zones || []).join(", ") || "none"}
            </span>
          </div>

          {(result.zone_risks || []).length > 0 && (
            <div>
              <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-mist">
                Zone forecast
              </div>
              <div className="space-y-1">
                {(result.zone_risks || []).slice(0, 4).map((z) => (
                  <div
                    key={z.zone_code}
                    className="flex items-center justify-between rounded border border-line/70 bg-soft/40 px-2 py-1 font-mono text-[11px]"
                  >
                    <span className="text-ink/90">
                      {z.zone_code}{" "}
                      <span className={bandClass(z.band)}>{(z.band || "").toUpperCase()}</span>
                    </span>
                    <span className="text-mist">DCRS {z.dcrs.toFixed(0)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(result.recommended_actions || []).length > 0 && (
            <div>
              <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-mist">
                Recommended actions
              </div>
              <ul className="space-y-1">
                {(result.recommended_actions || []).slice(0, 5).map((a, i) => (
                  <li
                    key={`${a.action_type}-${i}`}
                    className="rounded border border-line/70 bg-soft/40 px-2 py-1.5 text-xs text-ink/90"
                  >
                    <div className="flex justify-between gap-2">
                      <span>{a.title}</span>
                      {typeof a.confidence === "number" && (
                        <span className="shrink-0 font-mono text-[10px] text-accent">
                          {Math.round(a.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!result && !error && !loading && (
        <p className="mt-3 text-xs text-mist">
          Run a scenario to compare predicted risk against the live twin. Use{" "}
          <span className="text-ink/75">Demo: Close Gate-C</span> for the panel pitch.
        </p>
      )}
    </div>
  );
}
