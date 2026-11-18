from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.repository import VenueRepository, venue_to_dict
from app.infrastructure.persistence.seed import VENUE_ID, get_demo_venue

router = APIRouter()


@router.get("/")
async def list_venues(db: AsyncSession = Depends(get_db)):
    repo = VenueRepository(db)
    return await repo.list_venues()


@router.get("/demo")
async def demo_venue(db: AsyncSession = Depends(get_db)):
    venue = await get_demo_venue(db)
    if not venue:
        raise HTTPException(status_code=404, detail="Demo venue not found")
    return venue_to_dict(venue, include_cameras=True)


@router.get("/{venue_id}")
async def get_venue(venue_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = VenueRepository(db)
    venue = await repo.get_venue(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.get("/{venue_id}/zones")
async def list_zones(venue_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = VenueRepository(db)
    zones = await repo.list_zones(venue_id)
    if not zones and venue_id != VENUE_ID:
        # still return empty if venue missing
        venue = await repo.get_venue(venue_id)
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")
    return zones


@router.get("/{venue_id}/cameras")
async def list_cameras(venue_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = VenueRepository(db)
    venue = await repo.get_venue(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return await repo.list_cameras(venue_id)
