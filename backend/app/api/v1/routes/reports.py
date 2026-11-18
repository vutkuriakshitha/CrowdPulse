"""Incident report API — live twin + optional Ollama (Day 17)."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.reporting.incident_report import GenAIIncidentReporter, IncidentContext
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.models import IncidentReportModel
from app.infrastructure.persistence.twin_store import twin_store

router = APIRouter()


class ReportRequest(BaseModel):
    event_name: str | None = None
    venue_name: str | None = None
    peak_dcrs: float | None = None
    hotspot_zones: list[str] | None = None
    decisions_taken: list[str] | None = None
    timeline: list[dict] | None = None
    metrics_summary: dict | None = None
    use_live_twin: bool = True


def _build_live_context(body: ReportRequest) -> IncidentContext:
    venue_name = body.venue_name or twin_store.venue.get("name") or "Aether Arena"
    event_name = body.event_name or f"{venue_name} — Crowd Operations Log"

    # Zone cards from latest risks
    cards = list(twin_store.latest_risks.values())
    if not cards:
        # Force a lightweight evaluate path via stored metrics if present
        from app.application.use_cases.evaluate_risk import EvaluateVenueRiskUseCase

        snap = EvaluateVenueRiskUseCase().execute(clear_alerts=False)
        cards = snap.get("zones") or []
        alerts = snap.get("alerts") or twin_store.alerts
        peak_dcrs = float(snap.get("peak_dcrs") or body.peak_dcrs or 0.0)
        peak_zone = snap.get("peak_zone")
        peak_band = snap.get("peak_band")
    else:
        alerts = twin_store.alerts
        cards_sorted = sorted(cards, key=lambda c: c.get("risk", {}).get("dcrs", 0), reverse=True)
        peak_dcrs = float(body.peak_dcrs if body.peak_dcrs is not None else cards_sorted[0]["risk"]["dcrs"])
        peak_zone = cards_sorted[0]["zone"]["code"]
        peak_band = cards_sorted[0]["risk"]["band"]

    hotspots = body.hotspot_zones
    if hotspots is None:
        hotspots = [
            c["zone"]["code"]
            for c in sorted(cards, key=lambda x: x.get("risk", {}).get("dcrs", 0), reverse=True)
            if c.get("risk", {}).get("dcrs", 0) >= 60
        ][:4]
        if not hotspots and cards:
            hotspots = [sorted(cards, key=lambda x: x.get("risk", {}).get("dcrs", 0), reverse=True)[0]["zone"]["code"]]

    decisions = body.decisions_taken
    if decisions is None:
        decisions = []
        for alert in alerts[:20]:
            for act in alert.get("actions") or []:
                st = (act.get("status") or "pending").lower()
                if st in ("accepted", "dismissed", "executed"):
                    who = act.get("acked_by_name") or act.get("acked_by") or "operator"
                    decisions.append(
                        f"Zone {alert.get('zone_code')}: {act.get('title') or act.get('action_type')} "
                        f"[{st}] by {who}"
                    )
        # Also pending top recommendations for context
        if not decisions:
            for alert in alerts[:5]:
                for act in (alert.get("actions") or [])[:2]:
                    decisions.append(
                        f"Zone {alert.get('zone_code')}: recommended {act.get('title') or act.get('action_type')} "
                        f"(pending, conf={act.get('confidence', 0):.2f})"
                    )

    timeline = body.timeline
    if timeline is None:
        timeline = []
        # Alerts as timeline
        for alert in sorted(alerts[:12], key=lambda a: a.get("created_at") or 0):
            ts = alert.get("created_at")
            if isinstance(ts, (int, float)):
                tlabel = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")
            else:
                tlabel = "—"
            band = (alert.get("band") or "").upper()
            timeline.append(
                {
                    "t": tlabel,
                    "event": (
                        f"Zone {alert.get('zone_code')} {band} alert "
                        f"(DCRS {float(alert.get('dcrs') or 0):.1f})"
                    ),
                }
            )
        # Accepted actions
        for alert in alerts[:20]:
            for act in alert.get("actions") or []:
                if (act.get("status") or "").lower() != "accepted":
                    continue
                ts = act.get("acked_at")
                tlabel = (
                    datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")
                    if isinstance(ts, (int, float))
                    else "—"
                )
                timeline.append(
                    {
                        "t": tlabel,
                        "event": f"Accepted: {act.get('title') or act.get('action_type')} (Zone {alert.get('zone_code')})",
                    }
                )
        if not timeline:
            timeline = [
                {"t": datetime.now(timezone.utc).strftime("%H:%M"), "event": "Report generated from current twin state"},
                {
                    "t": "—",
                    "event": f"Peak zone {peak_zone or 'n/a'} at DCRS {peak_dcrs:.1f}",
                },
            ]

    metrics = body.metrics_summary
    if metrics is None:
        dens = []
        opp = []
        speeds = []
        for c in cards:
            m = c.get("metrics") or {}
            if "density" in m:
                dens.append(float(m["density"]))
            if "opposing_flow" in m:
                opp.append(float(m["opposing_flow"]))
            if "mean_speed" in m:
                speeds.append(float(m["mean_speed"]))
        metrics = {
            "peak_dcrs": round(peak_dcrs, 2),
            "peak_zone": peak_zone,
            "peak_band": peak_band,
            "max_density": round(max(dens), 3) if dens else None,
            "max_opposing_flow": round(max(opp), 3) if opp else None,
            "min_mean_speed": round(min(speeds), 3) if speeds else None,
            "open_alerts": len([a for a in alerts if a.get("queue_status", "open") == "open"]),
            "zones_evaluated": len(cards),
        }

    return IncidentContext(
        event_name=event_name,
        venue_name=venue_name,
        timeline=timeline,
        peak_dcrs=float(peak_dcrs),
        hotspot_zones=hotspots or [],
        decisions_taken=decisions or [],
        metrics_summary=metrics or {},
        peak_zone=peak_zone,
        peak_band=peak_band,
    )


@router.post("/incident")
async def generate_incident_report(
    body: ReportRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    body = body or ReportRequest()
    if body.use_live_twin:
        ctx = _build_live_context(body)
    else:
        ctx = IncidentContext(
            event_name=body.event_name or "Championship Final 2026",
            venue_name=body.venue_name or "Aether Arena",
            timeline=body.timeline
            or [
                {"t": "18:42", "event": "Zone B entered Orange band"},
                {"t": "18:47", "event": "Forecast surge predicted Red in 8 minutes"},
            ],
            peak_dcrs=float(body.peak_dcrs if body.peak_dcrs is not None else 91.0),
            hotspot_zones=body.hotspot_zones or ["B", "C"],
            decisions_taken=body.decisions_taken
            or ["Opened Gate-C", "Deployed guards to Central Bowl"],
            metrics_summary=body.metrics_summary
            or {"max_density": 4.1, "max_opposing_flow": 0.62},
            peak_zone=(body.hotspot_zones or ["B"])[0],
            peak_band="orange",
        )

    reporter = GenAIIncidentReporter()
    out = await reporter.generate(ctx)

    report_id = uuid4()
    persisted = False
    try:
        db.add(
            IncidentReportModel(
                id=report_id,
                event_name=ctx.event_name,
                venue_name=ctx.venue_name,
                markdown=out.markdown,
                pdf_uri=None,
            )
        )
        await db.commit()
        persisted = True
    except Exception:  # noqa: BLE001
        await db.rollback()

    return {
        "id": str(report_id) if persisted else None,
        "markdown": out.markdown,
        "format": "markdown",
        "source": out.source,
        "persisted": persisted,
        "generated_at": time.time(),
        "context": {
            "event_name": ctx.event_name,
            "venue_name": ctx.venue_name,
            "peak_dcrs": ctx.peak_dcrs,
            "peak_zone": ctx.peak_zone,
            "peak_band": ctx.peak_band,
            "hotspot_zones": ctx.hotspot_zones,
        },
    }


@router.get("/recent")
async def recent_reports(limit: int = 10, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    result = await db.execute(
        select(IncidentReportModel).order_by(IncidentReportModel.created_at.desc()).limit(min(limit, 50))
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "event_name": r.event_name,
            "venue_name": r.venue_name,
            "markdown": r.markdown,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
