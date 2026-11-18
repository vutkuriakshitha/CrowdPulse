"use client";

import { TwinZoneCard } from "@/services/api";

const BAND_COLOR: Record<string, string> = {
  green: "#2f9e6b",
  yellow: "#d4a017",
  orange: "#d97706",
  red: "#c43c3c",
};

const BAND_LABEL: Record<string, string> = {
  green: "G",
  yellow: "Y",
  orange: "O",
  red: "R",
};

export function DigitalTwinMap({
  zones,
  peakZoneCode,
  highlight = true,
}: {
  zones: TwinZoneCard[];
  peakZoneCode?: string | null;
  highlight?: boolean;
}) {
  const width = 640;
  const height = 360;
  const pad = 28;

  const allPts = zones.flatMap((z) => z.zone.polygon || []);
  const xs = allPts.map((p) => p[0]);
  const ys = allPts.map((p) => p[1]);
  const minX = Math.min(...xs, 0);
  const maxX = Math.max(...xs, 120);
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys, 55);

  const sx = (x: number) => pad + ((x - minX) / (maxX - minX || 1)) * (width - pad * 2);
  const sy = (y: number) => pad + ((y - minY) / (maxY - minY || 1)) * (height - pad * 2);

  const peak =
    peakZoneCode ||
    [...zones].sort((a, b) => b.risk.dcrs - a.risk.dcrs)[0]?.zone.code ||
    null;

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-[380px] w-full">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="hotGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* floor grid */}
        <rect x={0} y={0} width={width} height={height} fill="transparent" />

        {zones.map((z) => {
          const poly = (z.zone.polygon || []).map((p) => `${sx(p[0])},${sy(p[1])}`).join(" ");
          const band = z.risk.band || "green";
          const color = BAND_COLOR[band] || "#888";
          const isPeak = highlight && z.zone.code === peak;
          const isHot = band === "orange" || band === "red";
          const cx =
            (z.zone.polygon || []).reduce((a, p) => a + p[0], 0) /
            Math.max((z.zone.polygon || []).length, 1);
          const cy =
            (z.zone.polygon || []).reduce((a, p) => a + p[1], 0) /
            Math.max((z.zone.polygon || []).length, 1);

          return (
            <g key={z.zone.id} className="transition-all duration-700">
              <polygon
                points={poly}
                fill={color}
                fillOpacity={isHot ? 0.62 : 0.45}
                stroke={color}
                strokeWidth={isPeak ? 3.5 : 2}
                filter={isHot ? "url(#hotGlow)" : "url(#glow)"}
              />
              {/* DCRS badge */}
              <rect
                x={sx(cx) - 34}
                y={sy(cy) - 22}
                width={68}
                height={40}
                rx={6}
                fill="rgba(255,255,255,0.92)"
                stroke={color}
                strokeWidth={1.2}
              />
              <text
                x={sx(cx)}
                y={sy(cy) - 4}
                textAnchor="middle"
                fill="#132a44"
                fontSize={13}
                fontFamily="ui-monospace, monospace"
                fontWeight={600}
              >
                {z.zone.code} · {BAND_LABEL[band] || "?"}
              </text>
              <text
                x={sx(cx)}
                y={sy(cy) + 12}
                textAnchor="middle"
                fill={color}
                fontSize={14}
                fontFamily="ui-monospace, monospace"
                fontWeight={700}
              >
                {z.risk.dcrs.toFixed(0)}
              </text>
              <text
                x={sx(cx)}
                y={sy(cy) + 34}
                textAnchor="middle"
                fill="#5a7189"
                fontSize={10}
                fontFamily="ui-monospace, monospace"
              >
                {z.metrics.count} ppl · {z.metrics.density.toFixed(1)} dens
              </text>
            </g>
          );
        })}

        {!zones.length && (
          <text x={width / 2} y={height / 2} textAnchor="middle" fill="#5a7189" fontSize={14}>
            Waiting for twin snapshot…
          </text>
        )}
      </svg>

      <div className="absolute bottom-2 left-2 flex flex-wrap gap-2 rounded border border-line bg-panel/95 px-2 py-1 font-mono text-[10px] text-mist shadow-sm">
        {(["green", "yellow", "orange", "red"] as const).map((b) => (
          <span key={b} className="inline-flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: BAND_COLOR[b] }} />
            {b.toUpperCase()}
          </span>
        ))}
        {peak && <span className="text-ink/75">· peak {peak}</span>}
      </div>
    </div>
  );
}
