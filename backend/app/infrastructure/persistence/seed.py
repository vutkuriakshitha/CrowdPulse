"""Canonical demo venue + control-room user seed for CrowdPulse (idempotent)."""

from __future__ import annotations

from uuid import UUID, uuid5, NAMESPACE_DNS

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.infrastructure.persistence.models import CameraModel, UserModel, VenueModel, ZoneModel


def _zid(code: str) -> UUID:
    return uuid5(NAMESPACE_DNS, f"crowdpulse.zone.{code}")


VENUE_ID = uuid5(NAMESPACE_DNS, "crowdpulse.venue.aether")

DEMO_ZONES = [
    {
        "id": _zid("A"),
        "code": "A",
        "name": "North Concourse",
        "area_m2": 250.0,
        "capacity": 800,
        "exits": ["Gate-A", "Gate-B"],
        "adjacent": ["B", "C"],
        "is_ingress": True,
        "polygon": [[0, 0], [40, 0], [40, 20], [0, 20]],
    },
    {
        "id": _zid("B"),
        "code": "B",
        "name": "Central Bowl",
        "area_m2": 400.0,
        "capacity": 1600,
        "exits": ["Gate-B", "Gate-C"],
        "adjacent": ["A", "C", "D"],
        "is_ingress": False,
        "polygon": [[40, 0], [90, 0], [90, 30], [40, 30]],
    },
    {
        "id": _zid("C"),
        "code": "C",
        "name": "East Corridor",
        "area_m2": 180.0,
        "capacity": 500,
        "exits": ["Gate-C"],
        "adjacent": ["A", "B", "D"],
        "is_ingress": False,
        "polygon": [[90, 0], [120, 0], [120, 25], [90, 25]],
    },
    {
        "id": _zid("D"),
        "code": "D",
        "name": "South Plaza",
        "area_m2": 300.0,
        "capacity": 900,
        "exits": ["Gate-D", "Gate-E"],
        "adjacent": ["B", "C"],
        "is_ingress": True,
        "polygon": [[40, 30], [100, 30], [100, 55], [40, 55]],
    },
]

DEMO_CAMERAS = [
    {
        "code": "CAM-01",
        "stream_url": "rtsp://edge-1/cam01",
        "edge_node_id": "edge-1",
        "fps": 10,
        "homography": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    },
    {
        "code": "CAM-02",
        "stream_url": "rtsp://edge-1/cam02",
        "edge_node_id": "edge-1",
        "fps": 10,
        "homography": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    },
    {
        "code": "CAM-03",
        "stream_url": "rtsp://edge-2/cam03",
        "edge_node_id": "edge-2",
        "fps": 10,
        "homography": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    },
]


# Telangana control-room demo accounts (change passwords before any real handover).
CONTROL_ROOM_USERS = [
    {
        "username": "tsp.operator",
        "password": "Operator@TS2026",
        "full_name": "Control Room Operator",
        "role": "operator",
        "organization": "Telangana State Police",
        "unit": "Hyderabad Venue Control Room",
    },
    {
        "username": "tsp.admin",
        "password": "Admin@TS2026",
        "full_name": "Control Room Administrator",
        "role": "admin",
        "organization": "Telangana State Police",
        "unit": "Hyderabad Venue Control Room",
    },
    {
        "username": "stadium.ops",
        "password": "Stadium@TS2026",
        "full_name": "Stadium Operations Officer",
        "role": "operator",
        "organization": "Aether Arena Operations",
        "unit": "Match-Day Control Desk",
    },
]


async def seed_control_room_users(session: AsyncSession) -> int:
    """Idempotently seed TSP / stadium control-room accounts."""
    created = 0
    for u in CONTROL_ROOM_USERS:
        exists = await session.scalar(select(func.count()).select_from(UserModel).where(UserModel.username == u["username"]))
        if exists and exists > 0:
            continue
        session.add(
            UserModel(
                username=u["username"],
                password_hash=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                organization=u["organization"],
                unit=u["unit"],
                is_active=True,
            )
        )
        created += 1
    if created:
        await session.commit()
    return created


async def seed_demo_venue_if_empty(session: AsyncSession) -> bool:
    count = await session.scalar(select(func.count()).select_from(VenueModel))
    if count and count > 0:
        return False

    venue = VenueModel(
        id=VENUE_ID,
        name="Aether Arena",
        timezone="Asia/Kolkata",
        boundary={"type": "Polygon", "coordinates": [[[0, 0], [120, 0], [120, 55], [0, 55], [0, 0]]]},
    )
    session.add(venue)

    for z in DEMO_ZONES:
        session.add(
            ZoneModel(
                id=z["id"],
                venue_id=VENUE_ID,
                code=z["code"],
                name=z["name"],
                polygon=z["polygon"],
                area_m2=z["area_m2"],
                capacity=z["capacity"],
                exits=z["exits"],
                adjacent=z["adjacent"],
                is_ingress=z["is_ingress"],
            )
        )

    for c in DEMO_CAMERAS:
        session.add(
            CameraModel(
                venue_id=VENUE_ID,
                code=c["code"],
                stream_url=c["stream_url"],
                homography=c["homography"],
                fps=c["fps"],
                edge_node_id=c["edge_node_id"],
                is_active=True,
            )
        )

    await session.commit()
    return True


async def get_demo_venue(session: AsyncSession) -> VenueModel | None:
    result = await session.execute(
        select(VenueModel)
        .options(selectinload(VenueModel.zones), selectinload(VenueModel.cameras))
        .where(VenueModel.id == VENUE_ID)
    )
    venue = result.scalar_one_or_none()
    if venue:
        return venue
    # fallback: first venue
    result = await session.execute(
        select(VenueModel).options(selectinload(VenueModel.zones), selectinload(VenueModel.cameras))
    )
    return result.scalars().first()
