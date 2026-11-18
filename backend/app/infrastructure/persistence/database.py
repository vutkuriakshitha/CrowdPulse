"""Database engine and session factory for CrowdPulse.

Default local engine: SQLite (aiosqlite) for reliable laptop/dev runs.
Production/Docker: set DATABASE_URL to PostgreSQL asyncpg URL.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure local data directory exists for SQLite
_data_dir = Path(__file__).resolve().parents[3] / "data"
_data_dir.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create schema and seed canonical demo venue + control-room users if empty."""
    from app.infrastructure.persistence.models import Base
    from app.infrastructure.persistence.seed import seed_control_room_users, seed_demo_venue_if_empty

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready (%s)", settings.database_url.split("://", 1)[0])

    async with SessionLocal() as session:
        seeded = await seed_demo_venue_if_empty(session)
        if seeded:
            logger.info("Seeded CrowdPulse demo venue, zones, and cameras")
        else:
            logger.info("Demo venue already present — skip seed")

        users_created = await seed_control_room_users(session)
        if users_created:
            logger.info("Seeded %s Telangana control-room user(s)", users_created)
        else:
            logger.info("Control-room users already present — skip user seed")
