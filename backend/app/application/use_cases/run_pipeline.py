"""Day 12 — one-click end-to-end CrowdPulse pipeline."""

from __future__ import annotations

import logging
import shutil
import time
import uuid
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.process_video import ProcessVideoUseCase
from app.core.config import settings
from app.infrastructure.persistence.models import VideoAssetModel
from app.infrastructure.persistence.seed import VENUE_ID
from app.infrastructure.persistence.twin_store import twin_store
from app.infrastructure.storage.video_storage import LocalVideoStorage

logger = logging.getLogger(__name__)


class PipelineRunRequest(BaseModel):
    video_id: UUID | None = None
    sample_filename: str | None = Field(
        default="synthetic_crowd.mp4",
        description="Used when video_id is omitted; file under data/uploads/samples/",
    )
    use_latest_upload: bool = False
    frame_stride: int = Field(default_factory=lambda: settings.demo_frame_stride, ge=1, le=60)
    max_frames: int = Field(default_factory=lambda: settings.demo_max_frames, ge=5, le=400)
    include_twin: bool = True


class RunPipelineUseCase:
    """Orchestrate: resolve video → detect/track/analytics → DCRS → ERA → GB → twin."""

    STAGES = (
        "resolve_video",
        "detect_track_analytics",
        "dcrs_era_recommend",
        "twin_snapshot",
    )

    def __init__(self, session: AsyncSession):
        self.session = session
        self.storage = LocalVideoStorage()

    async def _latest_video(self) -> VideoAssetModel | None:
        result = await self.session.execute(
            select(VideoAssetModel).order_by(VideoAssetModel.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def _ensure_sample_video(self, filename: str) -> VideoAssetModel:
        samples_dir = Path(self.storage.root) / "samples"
        samples_dir.mkdir(parents=True, exist_ok=True)
        src = samples_dir / Path(filename).name

        if not src.exists():
            # Generate synthetic crowd clip on demand for demo one-click
            if Path(filename).name == "synthetic_crowd.mp4":
                import sys

                scripts_dir = Path(__file__).resolve().parents[3] / "scripts"
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                from make_synthetic_crowd_video import main as make_video

                make_video()
            if not src.exists():
                raise FileNotFoundError(
                    f"Sample not found: {filename}. Place a clip in {samples_dir}"
                )

        # Reuse existing registered sample with same original name if present
        existing = await self.session.execute(
            select(VideoAssetModel)
            .where(VideoAssetModel.original_filename == src.name)
            .order_by(VideoAssetModel.created_at.desc())
            .limit(1)
        )
        row = existing.scalar_one_or_none()
        if row and Path(row.storage_path).exists():
            return row

        asset_id = uuid.uuid4()
        dest_name = f"{asset_id.hex}{src.suffix.lower()}"
        dest = Path(self.storage.root) / dest_name
        shutil.copy2(src, dest)
        row = VideoAssetModel(
            id=asset_id,
            venue_id=VENUE_ID,
            original_filename=src.name,
            stored_filename=dest_name,
            content_type="video/mp4",
            size_bytes=dest.stat().st_size,
            storage_path=str(dest.resolve()),
            source="sample",
            status="uploaded",
            notes="Auto-registered by pipeline/run",
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def _resolve_video(self, req: PipelineRunRequest) -> VideoAssetModel:
        if req.video_id is not None:
            row = await self.session.get(VideoAssetModel, req.video_id)
            if not row:
                raise FileNotFoundError(f"Video not found: {req.video_id}")
            return row

        if req.use_latest_upload:
            row = await self._latest_video()
            if row:
                return row

        sample = req.sample_filename or "synthetic_crowd.mp4"
        return await self._ensure_sample_video(sample)

    async def execute(self, req: PipelineRunRequest) -> dict:
        started = time.perf_counter()
        stages: list[dict] = []
        logger.info(
            "pipeline.run start stride=%s max_frames=%s use_latest=%s",
            req.frame_stride,
            req.max_frames,
            req.use_latest_upload,
        )

        try:
            t0 = time.perf_counter()
            video = await self._resolve_video(req)
            stages.append(
                {
                    "name": "resolve_video",
                    "ok": True,
                    "ms": round((time.perf_counter() - t0) * 1000, 1),
                    "video_id": str(video.id),
                    "filename": video.original_filename,
                }
            )
            logger.info("pipeline.stage=resolve_video file=%s id=%s", video.original_filename, video.id)

            t1 = time.perf_counter()
            process = await ProcessVideoUseCase(self.session).execute(
                video.id,
                frame_stride=req.frame_stride,
                max_frames=req.max_frames,
            )
            stages.append(
                {
                    "name": "detect_track_analytics",
                    "ok": True,
                    "ms": round((time.perf_counter() - t1) * 1000, 1),
                    "engine": process.get("engine"),
                    "backend": process.get("backend"),
                    "tracker": process.get("tracker"),
                    "max_count": (process.get("summary") or {}).get("max_count"),
                    "unique_tracks": (process.get("summary") or {}).get("unique_tracks"),
                    "empty_detections": process.get("empty_detections"),
                }
            )
            stages.append(
                {
                    "name": "dcrs_era_recommend",
                    "ok": True,
                    "ms": 0.0,
                    "peak_dcrs": process.get("peak_dcrs"),
                    "peak_zone": process.get("peak_zone"),
                    "peak_band": process.get("peak_band"),
                    "alerts": len(process.get("alerts") or []),
                    "zones_scored": len(process.get("risk_by_zone") or {}),
                }
            )

            twin = None
            if req.include_twin:
                t2 = time.perf_counter()
                zone_cards = list(twin_store.latest_risks.values())
                zone_cards.sort(key=lambda c: c["risk"]["dcrs"], reverse=True)
                twin = {
                    "venue": twin_store.venue,
                    "zones": zone_cards,
                    "alerts": list(twin_store.alerts[:20]),
                    "generated_at": time.time(),
                    "peak_dcrs": process.get("peak_dcrs"),
                    "peak_zone": process.get("peak_zone"),
                    "peak_band": process.get("peak_band"),
                }
                stages.append(
                    {
                        "name": "twin_snapshot",
                        "ok": True,
                        "ms": round((time.perf_counter() - t2) * 1000, 1),
                        "zones": len(zone_cards),
                        "alerts": len(twin["alerts"]),
                    }
                )

            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            logger.info(
                "pipeline.run done elapsed_ms=%s peak=%s:%s empty=%s",
                elapsed_ms,
                process.get("peak_zone"),
                process.get("peak_band"),
                process.get("empty_detections"),
            )
            return {
                "ok": True,
                "pipeline": "crowdpulse.level_a",
                "stages": stages,
                "elapsed_ms": elapsed_ms,
                "video": process.get("video"),
                "run_id": process.get("run_id"),
                "engine": process.get("engine"),
                "backend": process.get("backend"),
                "tracker": process.get("tracker"),
                "summary": process.get("summary"),
                "zone_summary": process.get("zone_summary"),
                "zone_analytics": process.get("zone_analytics"),
                "risk_by_zone": process.get("risk_by_zone"),
                "peak_dcrs": process.get("peak_dcrs"),
                "peak_zone": process.get("peak_zone"),
                "peak_band": process.get("peak_band"),
                "alerts": process.get("alerts") or [],
                "timeline": process.get("timeline"),
                "twin": twin,
                "empty_detections": process.get("empty_detections"),
                "warning": process.get("warning"),
                "annotated_url": process.get("annotated_url"),
                "preview_url": process.get("preview_url"),
                "flow": [
                    "video",
                    "detect",
                    "track",
                    "zone_analytics",
                    "dcrs",
                    "era_explain",
                    "gb_recommend",
                    "twin",
                ],
            }
        except Exception:
            logger.exception("pipeline.run failed after stages=%s", [s.get("name") for s in stages])
            raise
