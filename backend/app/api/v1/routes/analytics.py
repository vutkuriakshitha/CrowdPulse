"""Analytics — hotspot ranking + crowd trends (Day 18)."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.risk.dcrs import DCRSEngine
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.models import DetectionRunModel, HistoricalHotspotModel, RiskSnapshotModel
from app.infrastructure.persistence.twin_store import twin_store

router = APIRouter()
_risk = DCRSEngine()


def _band(dcrs: float) -> str:
    return _risk.band(dcrs).value


def _estimate_dcrs(density: float, exit_pressure: float = 0.4) -> float:
    """Level-A chart estimate when per-frame DCRS is unavailable."""
    density_norm = min(2.0, density / 4.0)
    logit = -2.2 + 1.4 * density_norm + 1.3 * min(2.0, exit_pressure) + 0.6 * 0.45
    # mirror sigmoid-ish scale used by DCRS without full feature set
    import math

    dcrs = 100.0 / (1.0 + math.exp(-max(min(logit, 20.0), -20.0)))
    return round(dcrs, 2)


@router.get("/hotspots")
async def historical_hotspots(db: AsyncSession = Depends(get_db)):
    """Rank zones by blended historical hotspot prior + live risk."""
    rows = []
    for z in twin_store.venue.get("zones") or []:
        zid = z["id"]
        m = twin_store.metrics.get(zid)
        if not m:
            continue
        risk_card = twin_store.latest_risks.get(zid) or {}
        dcrs = float((risk_card.get("risk") or {}).get("dcrs") or 0.0)
        if not dcrs and m:
            dcrs = _estimate_dcrs(m.density, m.exit_pressure)
        band = (risk_card.get("risk") or {}).get("band") or _band(dcrs)
        hist = float(m.historical_hotspot)
        # Blend: history + live pressure (0..1 composite then rank)
        live_factor = min(1.0, dcrs / 100.0)
        rank_score = round(0.55 * hist + 0.45 * live_factor, 4)
        rows.append(
            {
                "zone_id": zid,
                "zone_code": z["code"],
                "zone_name": z["name"],
                "historical_score": hist,
                "rank_score": rank_score,
                "current_density": round(m.density, 3),
                "current_dcrs": round(dcrs, 2),
                "band": band,
                "mean_speed": round(m.mean_speed, 3),
                "opposing_flow": round(m.opposing_flow, 3),
                "exit_pressure": round(m.exit_pressure, 3),
                "congestion_index": round(m.forecast_surge, 3),
                "recommendation": (
                    "Pre-stage marshals and open secondary exit 15m before peak"
                    if hist >= 0.4 or dcrs >= 60 or m.density >= 2.0
                    else "Monitor with standard staffing"
                ),
            }
        )

    rows.sort(key=lambda r: (r["rank_score"], r["current_dcrs"]), reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    # Persist / refresh historical_hotspots table for audit
    try:
        for r in rows:
            zid = UUID(str(r["zone_id"]))
            existing = await db.execute(
                select(HistoricalHotspotModel)
                .where(
                    HistoricalHotspotModel.zone_id == zid,
                    HistoricalHotspotModel.event_phase == "peak",
                )
                .limit(1)
            )
            row = existing.scalars().first()
            if row:
                row.score = float(r["rank_score"])
                row.sample_count = int(row.sample_count or 0) + 1
            else:
                db.add(
                    HistoricalHotspotModel(
                        id=uuid4(),
                        zone_id=zid,
                        event_phase="peak",
                        score=float(r["rank_score"]),
                        sample_count=1,
                    )
                )
        await db.commit()
    except Exception:  # noqa: BLE001
        await db.rollback()

    return {"hotspots": rows, "count": len(rows)}


@router.get("/trends")
async def crowd_trends(
    zone: str | None = Query(default=None, description="Zone code, default = peak/live hot zone"),
    db: AsyncSession = Depends(get_db),
):
    """Density/DCRS trend — prefers latest video detection timeline, else synthetic twin series."""
    zones = twin_store.venue.get("zones") or []
    code_to_zone = {z["code"]: z for z in zones}
    peak_code = None
    if twin_store.latest_risks:
        peak = max(
            twin_store.latest_risks.values(),
            key=lambda c: c.get("risk", {}).get("dcrs", 0),
            default=None,
        )
        if peak:
            peak_code = peak.get("zone", {}).get("code")
    zone_code = (zone or peak_code or "B").upper()
    zmeta = code_to_zone.get(zone_code) or (zones[0] if zones else None)
    area = float((zmeta or {}).get("area_m2") or 100.0)
    zid = (zmeta or {}).get("id")

    # 1) Latest detection run timeline (real processed frames)
    result = await db.execute(
        select(DetectionRunModel)
        .where(DetectionRunModel.status == "completed")
        .order_by(DetectionRunModel.created_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if run and run.timeline:
        points = []
        m = twin_store.metrics.get(zid) if zid else None
        exit_p = float(m.exit_pressure) if m else 0.4
        for p in run.timeline:
            counts = p.get("zone_counts") or {}
            count = int(counts.get(zone_code, p.get("count") or 0))
            # FOV-ish density consistent with Level A process_video heuristic
            fov = max(6.0, min(area * 0.08, 20.0))
            density = round(count / fov, 3)
            dcrs = _estimate_dcrs(density, exit_p)
            points.append(
                {
                    "t": round(float(p.get("time_sec") or p.get("frame_index") or 0), 2),
                    "density": density,
                    "dcrs": dcrs,
                    "count": count,
                }
            )
        if points:
            return {
                "source": "detection_run",
                "zone_code": zone_code,
                "run_id": str(run.id),
                "points": points,
                "series": {"density": "people/m² (FOV)", "dcrs": "estimated from density"},
            }

    # 2) Risk snapshots history for zone
    if zid:
        snaps = await db.execute(
            select(RiskSnapshotModel)
            .where(RiskSnapshotModel.zone_id == UUID(str(zid)))
            .order_by(RiskSnapshotModel.created_at.asc())
            .limit(40)
        )
        snap_rows = snaps.scalars().all()
        if len(snap_rows) >= 2:
            points = []
            for i, s in enumerate(snap_rows):
                dens = float((s.metrics or {}).get("density") or 0)
                points.append(
                    {
                        "t": i,
                        "density": round(dens, 3),
                        "dcrs": round(float(s.dcrs), 2),
                        "band": s.band,
                    }
                )
            return {
                "source": "risk_snapshots",
                "zone_code": zone_code,
                "points": points,
                "series": {"density": "snapshot density", "dcrs": "persisted DCRS"},
            }

    # 3) Synthetic series seeded from live twin (demo when no video processed yet)
    m = twin_store.metrics.get(zid) if zid else None
    base_d = float(m.density) if m else 2.0
    base_p = float(m.exit_pressure) if m else 0.4
    card = twin_store.latest_risks.get(zid) if zid else None
    base_dcrs = float((card or {}).get("risk", {}).get("dcrs") or _estimate_dcrs(base_d, base_p))
    points = []
    for i in range(0, 16):
        density = round(max(0.2, base_d * (0.7 + i * 0.04)), 3)
        dcrs = round(min(99.0, base_dcrs * (0.65 + i * 0.03)), 2)
        points.append({"t": i, "density": density, "dcrs": dcrs})
    return {
        "source": "synthetic_twin",
        "zone_code": zone_code,
        "points": points,
        "series": {"density": "projected from twin", "dcrs": "projected from twin"},
        "hint": "Process a CCTV clip to replace this with detection-run trends.",
    }
