"""CCTV video ingest APIs."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthUser, get_current_user, require_admin, require_operator
from app.core.config import settings
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.models import DetectionRunModel, VideoAssetModel
from app.infrastructure.persistence.seed import VENUE_ID
from app.infrastructure.storage.video_storage import LocalVideoStorage, VideoStorageError
from app.application.use_cases.process_video import ProcessVideoUseCase
from app.ai.perception.detector import detector_status

logger = logging.getLogger(__name__)
router = APIRouter()
media_router = APIRouter()
storage = LocalVideoStorage()


class VideoOut(BaseModel):
    id: str
    venue_id: str | None = None
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    source: str
    status: str
    notes: str | None = None
    created_at: str | None = None
    storage_path: str | None = None


class RegisterSampleRequest(BaseModel):
    filename: str = Field(..., description="File name inside data/uploads/samples/")
    venue_id: str | None = None


def _to_out(row: VideoAssetModel, *, include_path: bool = False) -> VideoOut:
    return VideoOut(
        id=str(row.id),
        venue_id=str(row.venue_id) if row.venue_id else None,
        original_filename=row.original_filename,
        stored_filename=row.stored_filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        source=row.source,
        status=row.status,
        notes=row.notes,
        created_at=row.created_at.isoformat() if row.created_at else None,
        storage_path=row.storage_path if include_path else None,
    )


@router.post("/upload", response_model=VideoOut)
async def upload_video(
    file: UploadFile = File(...),
    venue_id: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_operator),
):
    try:
        saved = await storage.save_upload(file)
    except VideoStorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc

    vid = UUID(venue_id) if venue_id else VENUE_ID
    row = VideoAssetModel(
        id=saved["id"],
        venue_id=vid,
        original_filename=saved["original_filename"],
        stored_filename=saved["stored_filename"],
        content_type=saved["content_type"],
        size_bytes=saved["size_bytes"],
        storage_path=saved["storage_path"],
        source="upload",
        status="uploaded",
        notes=notes,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_out(row)


@router.get("/", response_model=list[VideoOut])
async def list_videos(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VideoAssetModel).order_by(VideoAssetModel.created_at.desc()).limit(min(limit, 200))
    )
    rows = result.scalars().all()
    return [_to_out(r) for r in rows]


@router.get("/samples")
async def list_samples():
    return {
        "samples": storage.list_sample_files(),
        "hint": "Place CCTV clips in backend/data/uploads/samples/ then register via POST /videos/samples/register",
    }


@router.post("/samples/register", response_model=VideoOut)
async def register_sample(
    body: RegisterSampleRequest,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_admin),
):
    import uuid as uuid_mod

    samples_dir = Path(storage.root) / "samples"
    src = samples_dir / Path(body.filename).name
    if not src.exists() or not src.is_file():
        raise HTTPException(status_code=404, detail=f"Sample not found: {body.filename}")

    try:
        storage.validate(src.name, None, src.stat().st_size)
    except VideoStorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    asset_id = uuid_mod.uuid4()
    dest_name = f"{asset_id.hex}{src.suffix.lower()}"
    dest = Path(storage.root) / dest_name
    shutil.copy2(src, dest)

    row = VideoAssetModel(
        id=asset_id,
        venue_id=UUID(body.venue_id) if body.venue_id else VENUE_ID,
        original_filename=src.name,
        stored_filename=dest_name,
        content_type="video/mp4",
        size_bytes=dest.stat().st_size,
        storage_path=str(dest.resolve()),
        source="sample",
        status="uploaded",
        notes="Registered from samples folder",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_out(row)


@router.get("/detector/status")
async def get_detector_status():
    return detector_status()


@router.get("/{video_id}", response_model=VideoOut)
async def get_video(video_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await db.get(VideoAssetModel, video_id)
    if not row:
        raise HTTPException(status_code=404, detail="Video not found")
    return _to_out(row, include_path=True)


@router.post("/{video_id}/queue", response_model=VideoOut)
async def queue_processing(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_operator),
):
    """Mark video ready for detection pipeline."""
    row = await db.get(VideoAssetModel, video_id)
    if not row:
        raise HTTPException(status_code=404, detail="Video not found")
    if row.status not in {"uploaded", "failed", "queued", "completed"}:
        raise HTTPException(status_code=409, detail=f"Cannot queue from status={row.status}")
    row.status = "queued"
    row.notes = ((row.notes or "") + " | queued for detection pipeline").strip(" |")
    await db.commit()
    await db.refresh(row)
    return _to_out(row)


@media_router.get("/{video_id}/annotated")
async def get_annotated_video(
    video_id: UUID,
    _: AuthUser = Depends(get_current_user),
):
    """Stream annotated MP4 with numbered person boxes (proof-of-detection).

    Auth via Bearer header *or* ?token= (needed for HTML5 <video src>).
    Mounted outside the global protected dependency so query-token works.
    """
    path = Path(settings.video_upload_dir) / "annotated" / f"{video_id}_annotated.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Annotated video not ready. Run Process / Pipeline first.")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{video_id}_annotated.mp4",
        headers={"Cache-Control": "no-store"},
    )


@media_router.get("/{video_id}/preview")
async def get_preview_frame(
    video_id: UUID,
    _: AuthUser = Depends(get_current_user),
):
    """Best annotated still frame (people counted with IDs)."""
    path = Path(settings.video_upload_dir) / "annotated" / f"{video_id}_preview.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Preview frame not ready. Run Process / Pipeline first.")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@router.post("/{video_id}/process")
async def process_video(
    video_id: UUID,
    frame_stride: int | None = None,
    max_frames: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_operator),
):
    """Run YOLO/HOG person detection and return count timeline."""
    stride = frame_stride if frame_stride is not None else settings.demo_frame_stride
    frames = max_frames if max_frames is not None else settings.demo_max_frames
    try:
        uc = ProcessVideoUseCase(db)
        return await uc.execute(video_id, frame_stride=stride, max_frames=frames)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("process endpoint failed video_id=%s", video_id)
        raise HTTPException(status_code=500, detail=f"Detection failed: {exc}") from exc


@router.get("/{video_id}/detections")
async def get_detections(video_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await db.get(VideoAssetModel, video_id)
    if not row:
        raise HTTPException(status_code=404, detail="Video not found")
    result = await db.execute(
        select(DetectionRunModel)
        .where(DetectionRunModel.video_id == video_id)
        .order_by(DetectionRunModel.created_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="No detection run yet. Call /process first.")
    summary = dict(run.summary or {})
    ann_path = Path(settings.video_upload_dir) / "annotated" / f"{video_id}_annotated.mp4"
    prev_path = Path(settings.video_upload_dir) / "annotated" / f"{video_id}_preview.jpg"
    annotated_url = summary.get("annotated_url") or (
        f"/api/v1/videos/{video_id}/annotated" if ann_path.exists() else None
    )
    preview_url = summary.get("preview_url") or (
        f"/api/v1/videos/{video_id}/preview" if prev_path.exists() else None
    )
    return {
        "video_id": str(video_id),
        "run_id": str(run.id),
        "engine": run.engine,
        "backend": run.backend,
        "status": run.status,
        "summary": summary,
        "timeline": run.timeline,
        "annotated_url": annotated_url,
        "preview_url": preview_url,
        "error": run.error,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }
