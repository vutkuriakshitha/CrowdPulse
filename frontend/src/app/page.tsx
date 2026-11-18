"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { DigitalTwinMap } from "@/components/digital-twin/DigitalTwinMap";
import { RiskCards } from "@/components/risk/RiskCards";
import { DecisionQueue } from "@/components/risk/DecisionQueue";
import { WhatIfPanel } from "@/components/simulation/WhatIfPanel";
import { TrendChart } from "@/components/analytics/TrendChart";
import { ReportPanel } from "@/components/reports/ReportPanel";
import { CameraStrip } from "@/components/cameras/CameraStrip";
import { VideoUploadPanel } from "@/components/cameras/VideoUploadPanel";
import { DetectionProofPlayer } from "@/components/cameras/DetectionProofPlayer";
import {
  ApiError,
  fetchDemoVenue,
  fetchDetections,
  fetchHealth,
  fetchTwinSnapshot,
  fetchVideos,
  HealthStatus,
  TwinSnapshot,
  Venue,
} from "@/services/api";
import { AuthUser, fetchMe, getToken } from "@/services/auth";

type DetectionProof = {
  videoId: string;
  annotatedUrl: string;
  previewUrl?: string | null;
  maxCount?: number | null;
  uniqueTracks?: number | null;
  filename?: string | null;
};

export default function HomePage() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [snap, setSnap] = useState<TwinSnapshot | null>(null);
  const [venue, setVenue] = useState<Venue | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [mapFlash, setMapFlash] = useState(false);
  const [pollMs, setPollMs] = useState(5000);
  const [proof, setProof] = useState<DetectionProof | null>(null);

  useEffect(() => {
    let alive = true;
    const goLogin = () => {
      // Hard redirect — soft router.replace can leave this screen stuck on "Checking…"
      window.location.replace("/login");
    };
    const boot = async () => {
      if (!getToken()) {
        goLogin();
        return;
      }
      try {
        const me = await fetchMe();
        if (!alive) return;
        setUser(me);
        setAuthChecked(true);
      } catch {
        // fetchMe already clears an invalid token; never keep a stale local user after /me 401
        if (alive) goLogin();
      }
    };
    boot();
    return () => {
      alive = false;
    };
  }, []);

  const refreshTwin = useCallback(async () => {
    const t = await fetchTwinSnapshot();
    setSnap(t);
    return t;
  }, []);

  useEffect(() => {
    if (!authChecked || !user) return;
    let alive = true;

    const load = async () => {
      try {
        const [h, v, t] = await Promise.all([
          fetchHealth(),
          fetchDemoVenue(),
          fetchTwinSnapshot(),
        ]);
        if (!alive) return;
        setHealth(h);
        setVenue(v);
        setSnap(t);
        setError(null);
      } catch (e) {
        if (!alive) return;
        const msg = e instanceof ApiError ? e.message : "Failed to load CrowdPulse console";
        setError(msg);
      } finally {
        if (alive) setLoading(false);
      }
    };

    load();
    const id = setInterval(load, pollMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [authChecked, user, pollMs]);

  const onTwinInvalidate = useCallback(
    async (hint?: TwinSnapshot | null) => {
      try {
        if (hint?.zones?.length) {
          setSnap(hint);
        } else {
          await refreshTwin();
        }
        setMapFlash(true);
        setPollMs(2000);
        window.setTimeout(() => setMapFlash(false), 1600);
        window.setTimeout(() => setPollMs(5000), 20000);
        setError(null);
      } catch (e) {
        const msg = e instanceof ApiError ? e.message : "Twin refresh failed";
        setError(msg);
      }
    },
    [refreshTwin],
  );

  const onDetectionReady = useCallback((next: DetectionProof) => {
    setProof(next);
  }, []);

  // Restore latest annotated proof after refresh
  useEffect(() => {
    if (!authChecked || !user) return;
    let alive = true;
    (async () => {
      try {
        const vids = await fetchVideos();
        for (const v of vids.slice(0, 12)) {
          try {
            const d = await fetchDetections(v.id);
            const ann =
              d.annotated_url ||
              (d.summary?.annotated_url as string | undefined) ||
              null;
            if (!ann) continue;
            const prev =
              d.preview_url ||
              (d.summary?.preview_url as string | undefined) ||
              `/api/v1/videos/${v.id}/preview`;
            if (!alive) return;
            setProof({
              videoId: v.id,
              annotatedUrl: ann,
              previewUrl: prev,
              maxCount: (d.summary?.max_count as number) ?? null,
              uniqueTracks: (d.summary?.unique_tracks as number) ?? null,
              filename: v.original_filename,
            });
            return;
          } catch {
            /* try next video */
          }
        }
      } catch {
        /* ignore */
      }
    })();
    return () => {
      alive = false;
    };
  }, [authChecked, user]);

  const maxRisk = useMemo(() => {
    if (!snap?.zones?.length) return 0;
    return Math.max(...snap.zones.map((z) => z.risk.dcrs));
  }, [snap]);

  const peakZone = useMemo(() => {
    if (!snap?.zones?.length) return null;
    return [...snap.zones].sort((a, b) => b.risk.dcrs - a.risk.dcrs)[0]?.zone.code ?? null;
  }, [snap]);

  const bandSummary = useMemo(() => {
    const counts = { green: 0, yellow: 0, orange: 0, red: 0 };
    for (const z of snap?.zones || []) {
      const b = z.risk.band;
      if (b in counts) counts[b as keyof typeof counts] += 1;
    }
    return counts;
  }, [snap]);

  if (!authChecked || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-mist">
        Checking control-room session…
      </div>
    );
  }

  return (
    <AppShell
      health={health}
      venue={venue}
      loading={loading}
      error={error}
      peakDcrs={maxRisk}
      lastUpdated={snap?.generated_at ?? null}
      user={user}
    >
      <div className="grid gap-4 lg:grid-cols-12">
        <section className="fx-enter fx-enter-d1 lg:col-span-12">
          <DetectionProofPlayer
            videoId={proof?.videoId}
            annotatedUrl={proof?.annotatedUrl}
            previewUrl={proof?.previewUrl}
            maxCount={proof?.maxCount}
            uniqueTracks={proof?.uniqueTracks}
            filename={proof?.filename}
          />
        </section>
        <section
          className={`panel panel-map grid-fade fx-enter fx-enter-d2 relative min-h-[420px] overflow-hidden p-3 lg:col-span-7 ${
            mapFlash ? "ring-2 ring-accent/60 map-flash-ring" : ""
          }`}
        >
          <div className="mb-2 flex items-center justify-between px-1">
            <h2 className="section-label text-sm font-semibold text-ink">
              Live Venue Twin
              <span className="ml-2 inline-flex items-center gap-1 font-mono text-[10px] font-normal text-signal-green">
                <span className="live-dot" />
                streaming
              </span>
            </h2>
            <span className="font-mono text-xs text-mist">
              {loading
                ? "connecting…"
                : `G${bandSummary.green} Y${bandSummary.yellow} O${bandSummary.orange} R${bandSummary.red}${
                    peakZone ? ` · peak ${peakZone}` : ""
                  }`}
            </span>
          </div>
          {loading && !snap ? (
            <div className="flex h-[380px] items-center justify-center text-sm text-mist">
              Loading twin from API…
            </div>
          ) : (
            <DigitalTwinMap zones={snap?.zones || []} peakZoneCode={peakZone} />
          )}
        </section>

        <section className="fx-enter fx-enter-d3 flex flex-col gap-4 lg:col-span-5">
          <RiskCards zones={snap?.zones || []} />
          <DecisionQueue
            alerts={snap?.alerts || []}
            onAcked={(alert) => {
              setSnap((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  alerts: prev.alerts.map((a) => (a.id === alert.id ? alert : a)),
                };
              });
            }}
          />
        </section>

        <section className="fx-enter fx-enter-d4 lg:col-span-5">
          <VideoUploadPanel
            onTwinInvalidate={onTwinInvalidate}
            onDetectionReady={(info) =>
              onDetectionReady({
                videoId: info.videoId,
                annotatedUrl: info.annotatedUrl,
                previewUrl: info.previewUrl,
                maxCount: info.maxCount,
                uniqueTracks: info.uniqueTracks,
                filename: info.filename,
              })
            }
          />
        </section>
        <section className="fx-enter fx-enter-d5 lg:col-span-7">
          <CameraStrip cameras={venue?.cameras || []} />
        </section>

        <section className="fx-enter fx-enter-d5 lg:col-span-4">
          <WhatIfPanel
            exits={Array.from(new Set((venue?.zones || []).flatMap((z) => z.exits || [])))}
            zoneCodes={(venue?.zones || []).map((z) => z.code)}
          />
        </section>
        <section className="fx-enter fx-enter-d6 lg:col-span-4">
          <TrendChart />
        </section>
        <section className="fx-enter fx-enter-d7 lg:col-span-4">
          <ReportPanel venueName={venue?.name} />
        </section>
      </div>
    </AppShell>
  );
}
