"""SQLAlchemy persistence models (SQLite + PostgreSQL compatible)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    """Control-room accounts (Telangana police / stadium ops)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # operator | admin
    organization: Mapped[str] = mapped_column(String(200), default="Telangana State Police")
    unit: Mapped[str] = mapped_column(String(120), default="Venue Control Room")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VenueModel(Base):
    __tablename__ = "venues"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    boundary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    zones = relationship("ZoneModel", back_populates="venue", cascade="all, delete-orphan")
    cameras = relationship("CameraModel", back_populates="venue", cascade="all, delete-orphan")


class ZoneModel(Base):
    __tablename__ = "zones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("venues.id"), index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    polygon: Mapped[list] = mapped_column(JSON, default=list)
    area_m2: Mapped[float] = mapped_column(Float, default=100.0)
    capacity: Mapped[int] = mapped_column(Integer, default=400)
    exits: Mapped[list] = mapped_column(JSON, default=list)
    adjacent: Mapped[list] = mapped_column(JSON, default=list)
    is_ingress: Mapped[bool] = mapped_column(Boolean, default=False)

    venue = relationship("VenueModel", back_populates="zones")
    __table_args__ = (UniqueConstraint("venue_id", "code", name="uq_zone_code"),)


class CameraModel(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("venues.id"), index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    stream_url: Mapped[str] = mapped_column(String(512), default="")
    homography: Mapped[list] = mapped_column(JSON, default=list)
    fps: Mapped[int] = mapped_column(Integer, default=10)
    edge_node_id: Mapped[str] = mapped_column(String(64), default="edge-1")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    venue = relationship("VenueModel", back_populates="cameras")
    __table_args__ = (UniqueConstraint("venue_id", "code", name="uq_camera_code"),)


class AlertModel(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("zones.id"), index=True)
    severity: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="open")
    dcrs: Mapped[float] = mapped_column(Float)
    band: Mapped[str] = mapped_column(String(16))
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DecisionModel(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("alerts.id"), index=True)
    rationale: Mapped[str] = mapped_column(Text, default="")
    actions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SimulationModel(Base):
    __tablename__ = "simulations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("venues.id"), index=True)
    scenario: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IncidentReportModel(Base):
    __tablename__ = "incident_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_name: Mapped[str] = mapped_column(String(200))
    venue_name: Mapped[str] = mapped_column(String(200))
    markdown: Mapped[str] = mapped_column(Text)
    pdf_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class HistoricalHotspotModel(Base):
    __tablename__ = "historical_hotspots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("zones.id"), index=True)
    event_phase: Mapped[str] = mapped_column(String(64), default="peak")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)


class VideoAssetModel(Base):
    __tablename__ = "video_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("venues.id"), nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="upload")  # upload | sample
    status: Mapped[str] = mapped_column(String(32), default="uploaded")  # uploaded | queued | processing | completed | failed
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DetectionRunModel(Base):
    __tablename__ = "detection_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("video_assets.id"), index=True)
    engine: Mapped[str] = mapped_column(String(64), default="")
    backend: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="completed")
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    timeline: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RiskSnapshotModel(Base):
    """Persisted DCRS evaluation per zone (from video pipeline or live evaluate)."""

    __tablename__ = "risk_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("zones.id"), index=True)
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("video_assets.id"), nullable=True, index=True
    )
    detection_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("detection_runs.id"), nullable=True, index=True
    )
    dcrs: Mapped[float] = mapped_column(Float)
    band: Mapped[str] = mapped_column(String(16))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(32), default="evaluate")  # evaluate | video
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
