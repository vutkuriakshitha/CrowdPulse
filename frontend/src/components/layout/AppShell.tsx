"use client";

import clsx from "clsx";
import { getApiBase, HealthStatus, Venue } from "@/services/api";
import { AuthUser, logout } from "@/services/auth";

type Props = {
  health: HealthStatus | null;
  venue: Venue | null;
  loading: boolean;
  error: string | null;
  peakDcrs: number;
  lastUpdated?: number | null;
  user?: AuthUser | null;
};

export function AppShell({
  health,
  venue,
  loading,
  error,
  peakDcrs,
  lastUpdated,
  user,
  children,
}: Props & { children: React.ReactNode }) {
  const apiOnline = !!health && (health.status === "ok" || health.status === "degraded");
  const dbOk = health?.database?.ok === true;
  const dcrsHot = peakDcrs >= 60;

  return (
    <div className="fx-shell min-h-screen">
      <div className="fx-atmosphere" aria-hidden>
        <span className="fx-orb fx-orb-a" />
        <span className="fx-orb fx-orb-b" />
        <span className="fx-orb fx-orb-c" />
      </div>

      <header className="shell-header fx-header">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-6">
          <div className="flex items-center gap-3">
            <div className="brand-mark flex h-11 w-11 items-center justify-center rounded-xl font-mono text-sm font-bold">
              CP
            </div>
            <div>
              <div className="flex items-center gap-2 text-base font-bold tracking-tight text-ink">
                CrowdPulse
                <span className="inline-flex items-center gap-1 rounded-full border border-signal-green/40 bg-signal-green/10 px-1.5 py-0.5 font-mono text-[10px] font-medium text-signal-green">
                  <span className="live-dot" />
                  LIVE
                </span>
              </div>
              <div className="font-mono text-[11px] text-mist">
                Telangana Venue Control · Crowd Decision Support
              </div>
            </div>
          </div>

          <nav className="flex flex-wrap items-center gap-2 text-xs">
            <StatusPill
              label="API"
              ok={apiOnline}
              detail={apiOnline ? health?.version || "online" : "offline"}
            />
            <StatusPill label="DB" ok={dbOk} detail={dbOk ? `${health?.database?.venues ?? 0} venue` : "down"} />
            <StatusPill
              label="Venue"
              ok={!!venue}
              detail={venue?.name || "loading"}
              tone={venue ? "accent" : "neutral"}
            />
            {user && (
              <div className="flex items-center gap-2 rounded-lg border border-teal/30 bg-teal/10 px-2.5 py-1">
                <div className="text-left">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-teal">
                    {user.role === "admin" ? "Admin" : "Operator"}
                  </div>
                  <div className="max-w-[160px] truncate font-medium text-ink">{user.full_name}</div>
                </div>
                <button
                  type="button"
                  onClick={() => logout()}
                  className="rounded-md border border-line bg-white/70 px-2 py-1 font-mono text-[10px] text-mist hover:border-accent hover:text-accent"
                >
                  Sign out
                </button>
              </div>
            )}
            <div className="rounded-lg border border-accent/25 bg-accent/10 px-2.5 py-1 font-mono text-accent">
              {getApiBase().replace("http://", "")}
            </div>
          </nav>
        </div>
      </header>

      <main className="relative z-[1] mx-auto max-w-[1600px] px-4 py-5 md:px-6 md:py-6">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div className="fx-enter fx-enter-d1">
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.22em] text-accent">
              Operations Console
            </p>
            <h1 className="mt-1 bg-gradient-to-r from-ink via-accent to-teal bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl">
              {venue?.name || "Venue Twin"}
            </h1>
            <p className="mt-1 max-w-2xl text-sm text-mist">
              {user
                ? `${user.organization} · ${user.unit}`
                : "Live zone risk, explainable alerts, and Gradient Boosting recommendations from CCTV analytics."}
            </p>
            {error && (
              <p className="mt-2 rounded-md border border-signal-orange/40 bg-signal-orange/15 px-3 py-2 text-sm text-signal-orange">
                {error}
              </p>
            )}
          </div>

          <div className="flex gap-3">
            <div className={clsx("panel kpi-dcrs fx-kpi fx-enter-d2 min-w-[128px] px-4 py-3 font-mono text-sm")}>
              <div className="text-xs font-medium text-mist">Peak DCRS</div>
              <div
                className={clsx(
                  "text-3xl font-bold tracking-tight",
                  dcrsHot ? "text-coral" : "text-amber",
                )}
              >
                {loading && !peakDcrs ? "—" : peakDcrs.toFixed(1)}
              </div>
            </div>
            <div className="panel kpi-zones fx-kpi fx-enter-d3 min-w-[148px] px-4 py-3 font-mono text-sm">
              <div className="text-xs font-medium text-teal">Zones / Cameras</div>
              <div className="text-3xl font-bold tracking-tight text-accent">
                {venue ? `${venue.zones.length} / ${venue.cameras.length}` : "—"}
              </div>
              {lastUpdated && (
                <div className="mt-1 text-[10px] text-mist">
                  updated {new Date(lastUpdated * 1000).toLocaleTimeString()}
                </div>
              )}
            </div>
          </div>
        </div>

        {children}
      </main>
    </div>
  );
}

function StatusPill({
  label,
  ok,
  detail,
  tone = "neutral",
}: {
  label: string;
  ok: boolean;
  detail: string;
  tone?: "neutral" | "accent";
}) {
  return (
    <div
      className={clsx(
        "flex items-center gap-2 rounded-lg border px-2.5 py-1.5 font-mono shadow-sm",
        ok ? "border-signal-green/50 bg-signal-green/15" : "border-signal-red/50 bg-signal-red/15",
        tone === "accent" && ok && "border-accent/50 bg-sky/20",
      )}
    >
      <span
        className={clsx(
          "h-2 w-2 rounded-full shadow-sm",
          ok ? "live-dot" : "bg-signal-red",
        )}
      />
      <span className="text-mist">{label}</span>
      <span className="font-semibold text-ink">{detail}</span>
    </div>
  );
}
