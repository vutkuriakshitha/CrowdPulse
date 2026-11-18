"use client";

import { useState } from "react";
import { ApiError, generateReport, IncidentReportResult } from "@/services/api";

type Props = {
  venueName?: string;
};

export function ReportPanel({ venueName }: Props) {
  const [report, setReport] = useState<IncidentReportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await generateReport({
        use_live_twin: true,
        venue_name: venueName,
        event_name: venueName ? `${venueName} — After-Action Report` : undefined,
      });
      setReport(data);
    } catch (e) {
      setReport(null);
      setError(e instanceof ApiError ? e.message : "Report service unavailable.");
    } finally {
      setLoading(false);
    }
  };

  const onDownload = () => {
    if (!report?.markdown) return;
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
    const blob = new Blob([report.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `crowdpulse-incident-report-${stamp}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const md = report?.markdown || "";
  const ctx = report?.context;

  return (
    <div className="panel panel-risk flex h-full max-h-[520px] flex-col overflow-hidden p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="section-label text-sm font-semibold text-ink">Incident Report</h2>
          <p className="font-mono text-[10px] text-mist/80">
            Live twin · timeline · risk · decisions
          </p>
        </div>
        <div className="flex gap-1.5">
          <button
            type="button"
            onClick={onGenerate}
            disabled={loading}
            className="rounded bg-accent px-2.5 py-1 text-xs font-semibold text-white hover:brightness-110 disabled:opacity-60"
          >
            {loading ? "Writing…" : "Generate"}
          </button>
          <button
            type="button"
            onClick={onDownload}
            disabled={!md}
            className="rounded border border-line px-2.5 py-1 text-xs text-mist hover:border-accent hover:text-ink disabled:opacity-40"
          >
            Download .md
          </button>
        </div>
      </div>

      {error && (
        <p className="mb-2 rounded border border-signal-red/40 bg-signal-red/10 px-2 py-1.5 text-xs text-signal-red">
          {error}
        </p>
      )}

      {report && (
        <div className="mb-2 flex flex-wrap gap-2 font-mono text-[10px] text-mist">
          <span className="rounded border border-line px-1.5 py-0.5">
            source: {report.source || "template"}
          </span>
          {typeof ctx?.peak_dcrs === "number" && (
            <span className="rounded border border-line px-1.5 py-0.5">
              peak {ctx.peak_dcrs.toFixed(1)}
              {ctx.peak_zone ? ` · ${ctx.peak_zone}` : ""}
              {ctx.peak_band ? ` · ${ctx.peak_band}` : ""}
            </span>
          )}
          {report.persisted && (
            <span className="rounded border border-signal-green/40 px-1.5 py-0.5 text-signal-green">
              saved
            </span>
          )}
        </div>
      )}

      <pre className="min-h-0 flex-1 overflow-auto whitespace-pre-wrap rounded border border-line bg-soft/50 p-2 font-mono text-[11px] text-ink/75">
        {md ||
          "Generate an after-action report from the live twin: peak risk, alert timeline, accepted/dismissed actions, and improvements."}
      </pre>
    </div>
  );
}
