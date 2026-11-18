"""Batch ingestion domain schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BatchVideoItemOut(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    zone_code: str
    status: str
    progress: float = 0.0
    frame_count: int = 0
    processed_frames: int = 0
    density: float = 0.0
    count: int = 0
    error: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


class BatchJobResponse(BaseModel):
    batch_id: str
    status: str
    total_files: int
    completed_files: int = 0
    failed_files: int = 0
    estimated_time_s: float = 0.0
    error: str | None = None
    created_at: str | None = None
    completed_at: str | None = None
    items: list[BatchVideoItemOut] = Field(default_factory=list)
