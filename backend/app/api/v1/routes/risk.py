from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.evaluate_risk import EvaluateVenueRiskUseCase
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.models import RiskSnapshotModel
from app.infrastructure.persistence.twin_store import twin_store

router = APIRouter()


@router.post("/evaluate")
async def evaluate_risk():
    return EvaluateVenueRiskUseCase().execute()


@router.get("/alerts")
async def list_alerts(limit: int = 20):
    return twin_store.alerts[:limit]


@router.get("/snapshots")
async def list_risk_snapshots(
    limit: int = Query(40, ge=1, le=200),
    video_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(RiskSnapshotModel).order_by(RiskSnapshotModel.created_at.desc()).limit(limit)
    if video_id is not None:
        q = (
            select(RiskSnapshotModel)
            .where(RiskSnapshotModel.video_id == video_id)
            .order_by(RiskSnapshotModel.created_at.desc())
            .limit(limit)
        )
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(r.id),
            "zone_id": str(r.zone_id),
            "video_id": str(r.video_id) if r.video_id else None,
            "detection_run_id": str(r.detection_run_id) if r.detection_run_id else None,
            "dcrs": r.dcrs,
            "band": r.band,
            "metrics": r.metrics,
            "features": r.features,
            "explanation": r.explanation,
            "source": r.source,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
