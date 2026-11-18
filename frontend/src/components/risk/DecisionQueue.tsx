"use client";

import { useState } from "react";
import { ackAction, TwinAction, TwinAlert } from "@/services/api";

function narrativeOf(a: TwinAlert): string {
  const e = a.explanation;
  if (!e) return "";
  if (typeof e === "string") return e;
  return e.narrative || "";
}

function topLabels(a: TwinAlert): string[] {
  const e = a.explanation;
  if (!e || typeof e === "string") return [];
  if (e.top_labels?.length) return e.top_labels;
  return (e.contributions || []).slice(0, 3).map((c) => c.label || c.feature);
}

function statusOf(act: TwinAction): string {
  return (act.status || "pending").toLowerCase();
}

type Props = {
  alerts: TwinAlert[];
  onAcked?: (alert: TwinAlert) => void;
};

export function DecisionQueue({ alerts, onAcked }: Props) {
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [local, setLocal] = useState<Record<string, TwinAlert>>({});

  const visible = alerts.map((a) => local[a.id] || a);

  const onAck = async (alert: TwinAlert, act: TwinAction, status: "accepted" | "dismissed") => {
    const key = `${alert.id}:${act.action_type}:${status}`;
    setBusyKey(key);
    setError(null);
    try {
      const res = await ackAction({
        alert_id: alert.id,
        action_type: act.action_type,
        status,
      });
      setLocal((prev) => ({ ...prev, [alert.id]: res.alert }));
      onAcked?.(res.alert);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update action status");
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <div className="panel panel-alert max-h-[420px] overflow-auto p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="section-label text-sm font-semibold text-ink">Decision Queue</h2>
        <span className="font-mono text-[10px] text-mist">GB · Accept / Dismiss</span>
      </div>
      {error && (
        <p className="mb-2 rounded border border-signal-red/40 bg-signal-red/10 px-2 py-1 text-xs text-signal-red">
          {error}
        </p>
      )}
      <div className="space-y-3">
        {visible.slice(0, 4).map((a) => {
          const why = narrativeOf(a);
          const labels = topLabels(a);
          const band = a.band || "";
          const bandCls =
            band === "red"
              ? "border-signal-red/40"
              : band === "orange"
                ? "border-signal-orange/40"
                : "border-line";
          const actions = (a.actions || []).slice(0, 5);
          const maxConf = Math.max(...actions.map((x) => x.confidence ?? 0), 0.01);
          return (
            <details
              key={a.id}
              className={`rounded-lg border bg-soft/50 p-3 open:bg-soft/70 ${bandCls}`}
              open={band === "red" || band === "orange"}
            >
              <summary className="cursor-pointer list-none">
                <div className="mb-1 flex justify-between font-mono text-xs text-mist">
                  <span>
                    Zone {a.zone_code}
                    {band ? ` · ${band.toUpperCase()}` : ""}
                  </span>
                  <span>DCRS {a.dcrs.toFixed(0)}</span>
                </div>
                {labels.length > 0 && (
                  <div className="mb-1 flex flex-wrap gap-1">
                    {labels.map((lab) => (
                      <span
                        key={lab}
                        className="rounded border border-line bg-soft/80 px-1.5 py-0.5 text-[10px] text-ink/75"
                      >
                        {lab}
                      </span>
                    ))}
                  </div>
                )}
                <div className="text-[11px] text-mist">
                  {actions.length} ranked actions — Accept or Dismiss for control-room log
                </div>
              </summary>
              {why && (
                <pre className="mt-2 whitespace-pre-wrap border-t border-line pt-2 font-mono text-[11px] text-ink/75">
                  {why}
                </pre>
              )}
              {a.rationale && <p className="mt-2 text-xs text-mist">{a.rationale}</p>}
              <div className="mt-2 space-y-2">
                {actions.map((act, idx) => {
                  const conf = typeof act.confidence === "number" ? act.confidence : 0;
                  const pct = Math.round(conf * 100);
                  const bar = Math.min(100, (conf / maxConf) * 100);
                  const st = statusOf(act);
                  const pending = st === "pending";
                  const acceptKey = `${a.id}:${act.action_type}:accepted`;
                  const dismissKey = `${a.id}:${act.action_type}:dismissed`;
                  return (
                    <div
                      key={act.action_type + act.title}
                      className="rounded border border-line/60 bg-soft/40 px-2 py-1.5"
                    >
                      <div className="flex items-start justify-between gap-2 text-sm text-ink/90">
                        <span>
                          <span className="font-mono text-[10px] text-mist">#{idx + 1}</span> {act.title}
                        </span>
                        <span className="shrink-0 font-mono text-[11px] text-accent">{pct}%</span>
                      </div>
                      <div className="mt-1 h-1.5 overflow-hidden rounded bg-soft">
                        <div className="h-full rounded bg-accent/80" style={{ width: `${bar}%` }} />
                      </div>
                      <div className="mt-1 flex flex-wrap items-center justify-between gap-2">
                        <div className="font-mono text-[10px] text-mist">{act.action_type}</div>
                        {!pending ? (
                          <div
                            className={
                              st === "accepted"
                                ? "font-mono text-[10px] text-signal-green"
                                : "font-mono text-[10px] text-mist"
                            }
                          >
                            {st.toUpperCase()}
                            {act.acked_by_name || act.acked_by
                              ? ` · ${act.acked_by_name || act.acked_by}`
                              : ""}
                          </div>
                        ) : (
                          <div className="flex gap-1.5">
                            <button
                              type="button"
                              disabled={busyKey === acceptKey || busyKey === dismissKey}
                              onClick={() => onAck(a, act, "accepted")}
                              className="rounded border border-signal-green/40 bg-signal-green/15 px-2 py-0.5 font-mono text-[10px] text-signal-green hover:bg-signal-green/25 disabled:opacity-50"
                            >
                              {busyKey === acceptKey ? "…" : "Accept"}
                            </button>
                            <button
                              type="button"
                              disabled={busyKey === acceptKey || busyKey === dismissKey}
                              onClick={() => onAck(a, act, "dismissed")}
                              className="rounded border border-line px-2 py-0.5 font-mono text-[10px] text-mist hover:border-signal-orange/50 hover:text-signal-orange disabled:opacity-50"
                            >
                              {busyKey === dismissKey ? "…" : "Dismiss"}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </details>
          );
        })}
        {!visible.length && (
          <p className="text-sm text-mist">
            No Orange/Red alerts yet. Admin: reset demo metrics or run pipeline to populate the queue.
          </p>
        )}
      </div>
    </div>
  );
}
