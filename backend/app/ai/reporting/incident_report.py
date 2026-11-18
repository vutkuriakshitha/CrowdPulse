"""GenAI incident report generator (Ollama-compatible) with template fallback."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

import httpx

from app.core.config import settings


@dataclass
class IncidentContext:
    event_name: str
    venue_name: str
    timeline: list[dict[str, Any]]
    peak_dcrs: float
    hotspot_zones: list[str]
    decisions_taken: list[str]
    metrics_summary: dict[str, Any]
    peak_zone: str | None = None
    peak_band: str | None = None


@dataclass
class IncidentReportOutput:
    markdown: str
    source: Literal["ollama", "template"] = "template"


class GenAIIncidentReporter:
    """Produces structured after-action reports via local LLM (Ollama)."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model

    def build_prompt(self, ctx: IncidentContext) -> str:
        return f"""You are an emergency operations analyst for a venue control room.
Write a professional after-action incident report for crowd safety.

Event: {ctx.event_name}
Venue: {ctx.venue_name}
Peak DCRS: {ctx.peak_dcrs}
Peak zone: {ctx.peak_zone or 'n/a'} ({ctx.peak_band or 'n/a'})
Hotspots: {', '.join(ctx.hotspot_zones)}
Decisions: {json.dumps(ctx.decisions_taken)}
Metrics: {json.dumps(ctx.metrics_summary)}
Timeline: {json.dumps(ctx.timeline)}

Return markdown with sections:
1. Executive Summary
2. Timeline of Critical Events
3. Risk Analysis
4. Interventions and Effectiveness
5. Recurring Congestion Hotspots
6. Suggested Improvements
Keep it concise and operational (control-room tone).
"""

    async def generate(self, ctx: IncidentContext) -> IncidentReportOutput:
        prompt = self.build_prompt(ctx)
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                data = resp.json()
                text = (data.get("response") or "").strip()
                if text:
                    return IncidentReportOutput(markdown=text, source="ollama")
        except Exception:
            pass
        return IncidentReportOutput(markdown=self._fallback(ctx), source="template")

    async def generate_markdown(self, ctx: IncidentContext) -> str:
        """Back-compat helper."""
        return (await self.generate(ctx)).markdown

    def _fallback(self, ctx: IncidentContext) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        timeline_lines = []
        for item in ctx.timeline:
            t = item.get("t") or item.get("time") or "—"
            event = item.get("event") or item.get("message") or json.dumps(item)
            timeline_lines.append(f"- **{t}** — {event}")
        if not timeline_lines:
            timeline_lines = ["- No timeline events recorded"]

        decisions = [f"- {d}" for d in ctx.decisions_taken] or ["- None recorded / pending acknowledgment"]
        hotspots = [f"- Zone {z}" for z in ctx.hotspot_zones] or ["- None"]

        metrics = ctx.metrics_summary or {}
        metrics_lines = [f"- **{k}**: {v}" for k, v in metrics.items()] or ["- n/a"]

        peak_line = f"{ctx.peak_dcrs:.1f}"
        if ctx.peak_zone:
            peak_line += f" (Zone {ctx.peak_zone}"
            if ctx.peak_band:
                peak_line += f", {ctx.peak_band.upper()}"
            peak_line += ")"

        return f"""# Incident Report — {ctx.event_name}

**Venue:** {ctx.venue_name}  
**Generated:** {ts}  
**Source:** CrowdPulse template (Ollama unavailable)

## 1. Executive Summary
Peak Dynamic Crowd Risk Score (DCRS) reached **{peak_line}** at {ctx.venue_name}.
Primary hotspot zones: {', '.join(ctx.hotspot_zones) or 'n/a'}.
Control-room recommendations were evaluated; accepted interventions are listed below.

## 2. Timeline of Critical Events
{chr(10).join(timeline_lines)}

## 3. Risk Analysis
{chr(10).join(metrics_lines)}

## 4. Interventions and Effectiveness
{chr(10).join(decisions)}

## 5. Recurring Congestion Hotspots
{chr(10).join(hotspots)}

## 6. Suggested Improvements
- Pre-open secondary exits 15 minutes before forecast orange band
- Increase marshal density on historically hot corridors
- Rehearse PA scripts for opposing-flow conflicts
- Calibrate DCRS weights after each major event
- Log Accept/Dismiss decisions for after-action review
"""
