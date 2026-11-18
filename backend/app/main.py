"""CrowdPulse API entrypoint."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.websockets.twin import twin_ws_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.infrastructure.persistence.database import SessionLocal, init_db
from app.infrastructure.persistence.seed import get_demo_venue
from app.infrastructure.persistence.repository import venue_to_dict
from app.infrastructure.persistence.twin_store import twin_store

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    await init_db()
    # Sync runtime twin cache from DB (single source of truth for venue topology)
    async with SessionLocal() as session:
        venue = await get_demo_venue(session)
        if venue:
            twin_store.load_venue(venue_to_dict(venue, include_cameras=True))
            logger.info("Twin store synced from database (%s zones)", len(venue.zones))

    # Day 21 — warm detector + GB recommender so first demo click is fast
    if settings.warm_models_on_startup:
        try:
            from app.ai.perception.detector import warm_detector
            from app.ai.decision.ml_recommender import warm_recommender

            det = warm_detector()
            rec = warm_recommender()
            logger.info(
                "Warmed models detector=%s/%s recommender=%s",
                det.get("backend"),
                det.get("engine"),
                rec.get("algorithm") or rec.get("model") or "gb",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Model warmup skipped: %s", exc)
    yield


app = FastAPI(
    title="CrowdPulse API",
    description="Intelligent crowd analytics and decision support platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(twin_ws_router)


@app.get("/health")
async def health():
    db_ok = False
    venue_count = 0
    try:
        from sqlalchemy import func, select
        from app.infrastructure.persistence.models import VenueModel

        async with SessionLocal() as session:
            venue_count = int(await session.scalar(select(func.count()).select_from(VenueModel)) or 0)
            db_ok = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Health DB check failed: %s", exc)

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "crowdpulse",
        "version": "1.0.0",
        "database": {"ok": db_ok, "venues": venue_count},
    }
