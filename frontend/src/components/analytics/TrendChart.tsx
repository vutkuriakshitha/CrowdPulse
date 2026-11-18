"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { fetchTrends, TrendResponse } from "@/services/api";
import { HotspotPanel } from "@/components/analytics/HotspotPanel";

export function TrendChart() {
  const [data, setData] = useState<TrendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () => {
      fetchTrends()
        .then((d) => {
          if (!alive) return;
          setData(d);
          setError(null);
        })
        .catch(() => {
          if (!alive) return;
          setData(null);
          setError("Trends unavailable");
        });
    };
    load();
    const id = window.setInterval(load, 10000);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, []);

  const points = data?.points || [];
  const zone = data?.zone_code || "—";
  const source = data?.source || "—";

  return (
    <div className="panel panel-teal flex h-full max-h-[520px] flex-col overflow-hidden p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="section-label text-sm font-semibold text-ink">Analytics · Hotspots & Trends</h2>
        <span className="font-mono text-[10px] text-mist">
          Zone {zone} · {source}
        </span>
      </div>

      <HotspotPanel />

      <div className="mt-3 border-t border-line pt-2">
        <div className="mb-1 flex items-center justify-between">
          <h3 className="font-mono text-[10px] uppercase tracking-wider text-mist">
            Density / DCRS trend
          </h3>
          {data?.hint && <span className="max-w-[55%] truncate font-mono text-[9px] text-mist/70">{data.hint}</span>}
        </div>
        {error && <p className="mb-1 text-[11px] text-signal-orange">{error}</p>}
        <div className="h-[180px]">
          {points.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={points}>
                <CartesianGrid stroke="#c5d8eb" strokeDasharray="3 3" />
                <XAxis dataKey="t" stroke="#5a7189" fontSize={10} tickLine={false} />
                <YAxis stroke="#5a7189" fontSize={10} tickLine={false} width={32} />
                <Tooltip
                  contentStyle={{
                    background: "#ffffff",
                    border: "1px solid #c5d8eb",
                    color: "#132a44",
                    fontSize: 11,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 10, color: "#5a7189" }} />
                <Line
                  type="monotone"
                  dataKey="density"
                  name="Density"
                  stroke="#1577e0"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="dcrs"
                  name="DCRS"
                  stroke="#ea580c"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-mist">
              {error || "Waiting for trend data…"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
