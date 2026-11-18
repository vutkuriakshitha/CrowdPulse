"""Venue/zone/camera repository — DB-backed access layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.persistence.models import CameraModel, VenueModel, ZoneModel


def venue_to_dict(venue: VenueModel, *, include_cameras: bool = True) -> dict:
    zones = sorted(venue.zones, key=lambda z: z.code)
    payload = {
        "id": str(venue.id),
        "name": venue.name,
        "timezone": venue.timezone,
        "boundary": venue.boundary or {},
        "created_at": venue.created_at.isoformat() if venue.created_at else None,
        "zones": [
            {
                "id": str(z.id),
                "code": z.code,
                "name": z.name,
                "polygon": z.polygon or [],
                "area_m2": z.area_m2,
                "capacity": z.capacity,
                "exits": z.exits or [],
                "adjacent": z.adjacent or [],
                "is_ingress": z.is_ingress,
            }
            for z in zones
        ],
    }
    if include_cameras:
        cams = sorted(venue.cameras, key=lambda c: c.code)
        payload["cameras"] = [
            {
                "id": str(c.id),
                "code": c.code,
                "stream_url": c.stream_url,
                "fps": c.fps,
                "edge_node_id": c.edge_node_id,
                "is_active": c.is_active,
                "homography": c.homography or [],
            }
            for c in cams
        ]
    return payload


class VenueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_venues(self) -> list[dict]:
        result = await self.session.execute(
            select(VenueModel).options(
                selectinload(VenueModel.zones),
                selectinload(VenueModel.cameras),
            )
        )
        venues = result.scalars().unique().all()
        return [venue_to_dict(v) for v in venues]

    async def get_venue(self, venue_id: UUID) -> dict | None:
        result = await self.session.execute(
            select(VenueModel)
            .options(selectinload(VenueModel.zones), selectinload(VenueModel.cameras))
            .where(VenueModel.id == venue_id)
        )
        venue = result.scalar_one_or_none()
        return venue_to_dict(venue) if venue else None

    async def list_zones(self, venue_id: UUID) -> list[dict]:
        venue = await self.get_venue(venue_id)
        return venue["zones"] if venue else []

    async def list_cameras(self, venue_id: UUID) -> list[dict]:
        result = await self.session.execute(
            select(CameraModel).where(CameraModel.venue_id == venue_id).order_by(CameraModel.code)
        )
        cams = result.scalars().all()
        return [
            {
                "id": str(c.id),
                "code": c.code,
                "stream_url": c.stream_url,
                "fps": c.fps,
                "edge_node_id": c.edge_node_id,
                "is_active": c.is_active,
                "homography": c.homography or [],
            }
            for c in cams
        ]

    async def get_zone(self, zone_id: UUID) -> dict | None:
        result = await self.session.execute(select(ZoneModel).where(ZoneModel.id == zone_id))
        z = result.scalar_one_or_none()
        if not z:
            return None
        return {
            "id": str(z.id),
            "venue_id": str(z.venue_id),
            "code": z.code,
            "name": z.name,
            "polygon": z.polygon or [],
            "area_m2": z.area_m2,
            "capacity": z.capacity,
            "exits": z.exits or [],
            "adjacent": z.adjacent or [],
            "is_ingress": z.is_ingress,
        }
