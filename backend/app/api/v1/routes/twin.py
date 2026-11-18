from fastapi import APIRouter, Depends

from app.api.deps import AuthUser, require_admin
from app.application.use_cases.evaluate_risk import EvaluateVenueRiskUseCase
from app.infrastructure.persistence.twin_store import twin_store

router = APIRouter()


@router.get("/snapshot")
async def twin_snapshot():
    uc = EvaluateVenueRiskUseCase()
    return uc.execute()


@router.get("/zones")
async def twin_zones():
    return twin_store.venue["zones"]


@router.post("/reset-metrics")
async def reset_demo_metrics(_: AuthUser = Depends(require_admin)):
    """Restore seeded demo densities (Zone B hot) and re-run DCRS. Admin only."""
    twin_store._seed_metrics()
    return EvaluateVenueRiskUseCase().execute(clear_alerts=True)
