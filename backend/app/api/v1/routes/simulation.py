"""What-if simulation API (Day 15)."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.forecasting.zone_forecaster import ZoneGraphForecaster
from app.ai.risk.dcrs import DCRSEngine
from app.ai.simulation.what_if import WhatIfSimulator
from app.domain.entities.crowd import SimulationScenario
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.models import SimulationModel
from app.infrastructure.persistence.seed import VENUE_ID
from app.infrastructure.persistence.twin_store import twin_store

router = APIRouter()


@router.post("/what-if")
async def run_what_if(
    scenario: SimulationScenario,
    db: AsyncSession = Depends(get_db),
):
    if not twin_store.metrics:
        raise HTTPException(status_code=503, detail="Twin metrics not loaded")

    sim = WhatIfSimulator(
        forecaster=ZoneGraphForecaster(twin_store.adjacency()),
        risk_engine=DCRSEngine(),
    )
    result = sim.run(
        scenario=scenario,
        base_metrics=twin_store.metrics,
        zone_meta=twin_store.zone_meta_by_id(),
    )

    sim_id = uuid4()
    result.simulation_id = str(sim_id)
    payload = result.model_dump(mode="json")

    try:
        venue_raw = twin_store.venue.get("id") or str(VENUE_ID)
        venue_id = UUID(str(venue_raw))
        db.add(
            SimulationModel(
                id=sim_id,
                venue_id=venue_id,
                scenario=payload.get("scenario") or scenario.model_dump(mode="json"),
                result={
                    "predicted_peak_dcrs": result.predicted_peak_dcrs,
                    "baseline_peak_dcrs": result.baseline_peak_dcrs,
                    "dcrs_delta": result.dcrs_delta,
                    "congested_zones": result.congested_zones,
                    "narrative": result.narrative,
                    "zone_risks": result.zone_risks,
                    "recommended_actions": [
                        a.model_dump(mode="json") for a in result.recommended_actions
                    ],
                },
                status="completed",
            )
        )
        await db.commit()
        payload["persisted"] = True
    except Exception:  # noqa: BLE001
        await db.rollback()
        payload["persisted"] = False

    return payload


@router.get("/recent")
async def recent_simulations(limit: int = 10, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    result = await db.execute(
        select(SimulationModel).order_by(SimulationModel.created_at.desc()).limit(min(limit, 50))
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "venue_id": str(r.venue_id),
            "scenario": r.scenario,
            "result": r.result,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
