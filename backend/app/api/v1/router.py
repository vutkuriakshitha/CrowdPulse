from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.routes import (
    analytics,
    auth,
    decisions,
    pipeline,
    reports,
    risk,
    simulation,
    system,
    twin,
    venues,
    videos,
)

api_router = APIRouter()

# Public auth endpoints (login)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Media proof streams — auth via Bearer *or* ?token= (HTML5 video cannot send headers)
api_router.include_router(videos.media_router, prefix="/videos", tags=["videos-media"])

# All ops APIs require a valid control-room JWT
_protected = [Depends(get_current_user)]
api_router.include_router(system.router, tags=["system"], dependencies=_protected)
api_router.include_router(venues.router, prefix="/venues", tags=["venues"], dependencies=_protected)
api_router.include_router(videos.router, prefix="/videos", tags=["videos"], dependencies=_protected)
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"], dependencies=_protected)
api_router.include_router(twin.router, prefix="/twin", tags=["twin"], dependencies=_protected)
api_router.include_router(risk.router, prefix="/risk", tags=["risk"], dependencies=_protected)
api_router.include_router(decisions.router, prefix="/decisions", tags=["decisions"], dependencies=_protected)
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"], dependencies=_protected)
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"], dependencies=_protected)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"], dependencies=_protected)
