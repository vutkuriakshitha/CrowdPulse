"""Batch video ingestion and multi-camera zone processing engine.

Each tagged video assigns ALL its detections to its zone (skip the polygon ZoneAssigner).
Density = count / zone area_m2.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import logging
from pathlib import Path
import time
from uuid import UUID

import cv2
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.perception.detector import get_person_detector
from app.ai.perception.tracker import CentroidTracker
from app.application.use_cases.evaluate_risk import EvaluateVenueRiskUseCase
from app.core.config import settings
from app.domain.entities.crowd import ZoneMetrics
from app.infrastructure.persistence.database import SessionLocal
from app.infrastructure.persistence.models import (
    BatchJobModel,
    BatchVideoItemModel,
    VenueModel,
)
from app.infrastructure.persistence.seed import VENUE_ID, get_demo_venue
from app.infrastructure.persistence.twin_store import twin_store

logger = logging.getLogger(__name__)

# Shared 2-worker executor so YOLO is strictly offloaded from the asyncio event loop
_BATCH_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="batch-yolo")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def estimate_batch_processing_time(
    frame_counts: list[int],
    stride: int = 4,
    fps_per_worker: float = 5.5,
) -> float:
    """Compute estimated batch processing time based on actual video frame counts.

    With 2 parallel workers running YOLOv8n at ~5.5 FPS per worker:
    T_est = max( sum(sampled_frames) / (2 * fps_per_worker), max(sampled_frames) / fps_per_worker )
    """
    if not frame_counts:
        return 0.0
    sampled = [max(1, int(np.ceil(fc / max(1, stride)))) for fc in frame_counts if fc > 0]
    if not sampled:
        return 0.0
    total_sampled = sum(sampled)
    max_sampled = max(sampled)
    est = max(total_sampled / (2.0 * fps_per_worker), max_sampled / fps_per_worker)
    return round(float(est), 1)


def process_tagged_video_sync(
    storage_path: str,
    zone_code: str,
    zone_area_m2: float,
    frame_stride: int = 4,
    max_frames: int | None = None,
) -> dict:
    """Process a single CCTV video tagged to a specific venue zone.

    Each tagged video assigns ALL its detections to its zone (skip the polygon ZoneAssigner).
    Density = count / zone area_m2.
    """
    path = Path(storage_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path.name}")
    if path.stat().st_size <= 0:
        raise ValueError(f"Video file is empty: {path.name}")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video (unsupported or corrupt): {path.name}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    if width <= 0 or height <= 0:
        cap.release()
        raise ValueError(f"Video has invalid dimensions: {path.name}")

    detector = get_person_detector()
    tracker = CentroidTracker(max_lost=20, iou_threshold=0.15, dist_threshold=60.0)

    counts: list[int] = []
    frame_speeds: list[float] = []
    frame_headings: list[float] = []
    prev_centroids: dict[int, tuple[float, float, float]] = {}  # tid -> (x, y, t_sec)

    frame_idx = 0
    processed = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_idx += 1

            if (frame_idx - 1) % frame_stride != 0:
                continue

            if frame is None or not isinstance(frame, np.ndarray):
                continue

            detections = detector.detect(frame)
            active = tracker.update(detections)

            # ALL detections in this video are assigned directly to its tagged zone
            frame_count = len(active)
            counts.append(frame_count)

            t_sec = frame_idx / fps if fps > 0 else float(frame_idx)
            for t in active:
                c_x = (t.bbox[0] + t.bbox[2]) / 2.0
                c_y = (t.bbox[1] + t.bbox[3]) / 2.0
                if t.track_id in prev_centroids:
                    px, py, pt = prev_centroids[t.track_id]
                    dt = max(t_sec - pt, 1e-3)
                    # Ground proxy: normalize by frame height (assuming ~15m vertical FOV)
                    dist_px = float(np.hypot(c_x - px, c_y - py))
                    dist_m = (dist_px / max(height, 1)) * 15.0
                    speed = max(0.0, min(dist_m / dt, 4.0))
                    heading = float(np.arctan2(c_y - py, c_x - px))
                    frame_speeds.append(speed)
                    frame_headings.append(heading)
                prev_centroids[t.track_id] = (c_x, c_y, t_sec)

            processed += 1
            if max_frames and processed >= max_frames:
                break
    finally:
        cap.release()

    peak_count = int(max(counts)) if counts else 0
    effective_area = max(1.0, float(zone_area_m2))
    # Requirement 4: Density = count / zone area_m2
    density = round(float(peak_count) / effective_area, 4)

    mean_speed = float(np.mean(frame_speeds)) if frame_speeds else 1.0
    opposing = 0.0
    if len(frame_headings) >= 2:
        arr = np.asarray(frame_headings)
        R = float(np.hypot(np.mean(np.cos(arr)), np.mean(np.sin(arr))))
        opposing = float(np.clip(1.0 - R, 0.0, 1.0))

    congestion = min(1.5, density / 2.5)

    return {
        "ok": True,
        "zone_code": zone_code,
        "count": peak_count,
        "density": density,
        "processed_frames": processed,
        "total_frames": total_video_frames,
        "mean_speed": round(mean_speed, 3),
        "opposing_flow": round(opposing, 3),
        "congestion_index": round(congestion, 3),
        "abnormal_motion": 0.0,
        "error": None,
    }


async def run_batch_job(
    batch_id: UUID,
    venue_id: UUID | None = None,
    frame_stride: int | None = None,
    max_frames: int | None = None,
) -> None:
    """Async coordinator for batch video processing.

    1. Resets all zones to no_data before starting.
    2. Runs YOLO + CentroidTracker per video in ThreadPoolExecutor(max_workers=2).
    3. Handles per-video failures gracefully without failing the entire batch.
    4. Updates database status on BatchJobModel and BatchVideoItemModel.
    5. Populates twin_store per zone and executes EvaluateVenueRiskUseCase.
    """
    logger.info("Starting batch job %s for venue %s", batch_id, venue_id)

    # Requirement 6: A new batch first resets all zones to no_data
    twin_store.reset_all_to_no_data()

    async with SessionLocal() as session:
        job = await session.get(BatchJobModel, batch_id)
        if not job:
            logger.error("BatchJob %s not found in DB", batch_id)
            return

        job.status = "processing"
        await session.commit()

        # Load items
        q = select(BatchVideoItemModel).where(BatchVideoItemModel.batch_id == batch_id)
        res = await session.execute(q)
        items = list(res.scalars().all())

        # Load venue zone metadata
        vid = venue_id or job.venue_id or VENUE_ID
        v_res = await session.execute(
            select(VenueModel).options(selectinload(VenueModel.zones)).where(VenueModel.id == vid)
        )
        venue_row = v_res.scalar_one_or_none()
        if not venue_row:
            venue_row = await get_demo_venue(session)

        zone_area_map: dict[str, float] = {}
        zone_id_map: dict[str, str] = {}
        if venue_row and venue_row.zones:
            for z in venue_row.zones:
                zone_area_map[z.code] = float(z.area_m2 or 100.0)
                zone_id_map[z.code] = str(z.id)
        else:
            for z in twin_store.venue.get("zones", []):
                zone_area_map[z["code"]] = float(z.get("area_m2") or 100.0)
                zone_id_map[z["code"]] = str(z["id"])

    # Process items using thread pool executor
    loop = asyncio.get_running_loop()

    async def _process_item_wrapper(item_data: dict) -> dict:
        item_id = item_data["id"]
        storage_path = item_data["storage_path"]
        zone_code = item_data["zone_code"]
        area_m2 = zone_area_map.get(zone_code, 100.0)

        async with SessionLocal() as s:
            it = await s.get(BatchVideoItemModel, item_id)
            if it:
                it.status = "processing"
                it.progress = 10.0
                await s.commit()

        try:
            # Run YOLO inference off the asyncio event loop in thread pool
            eff_stride = frame_stride if frame_stride is not None else settings.demo_frame_stride
            result = await loop.run_in_executor(
                _BATCH_EXECUTOR,
                process_tagged_video_sync,
                storage_path,
                zone_code,
                area_m2,
                eff_stride,
                max_frames,
            )
            result["item_id"] = item_id
            return result
        except Exception as exc:
            logger.exception("Failed processing video item %s (file: %s)", item_id, storage_path)
            return {
                "ok": False,
                "item_id": item_id,
                "zone_code": zone_code,
                "error": str(exc),
                "count": 0,
                "density": 0.0,
                "processed_frames": 0,
            }

    tasks = [
        _process_item_wrapper({
            "id": it.id,
            "storage_path": it.storage_path,
            "zone_code": it.zone_code,
        })
        for it in items
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    completed_count = 0
    failed_count = 0
    successful_zones: list[dict] = []

    async with SessionLocal() as session:
        for r in results:
            if isinstance(r, Exception):
                logger.error("Unexpected worker exception: %s", r)
                failed_count += 1
                continue

            item_id = r["item_id"]
            it = await session.get(BatchVideoItemModel, item_id)
            if not it:
                continue

            if r.get("ok"):
                it.status = "completed"
                it.progress = 100.0
                it.count = r.get("count", 0)
                it.density = r.get("density", 0.0)
                it.processed_frames = r.get("processed_frames", 0)
                it.completed_at = utcnow()
                completed_count += 1
                successful_zones.append(r)
            else:
                it.status = "failed"
                it.progress = 0.0
                it.error = r.get("error") or "Video processing failed"
                it.completed_at = utcnow()
                failed_count += 1

        # Update overall job status
        job = await session.get(BatchJobModel, batch_id)
        if job:
            job.completed_files = completed_count
            job.failed_files = failed_count
            job.completed_at = utcnow()
            if failed_count == 0:
                job.status = "completed"
            elif completed_count > 0:
                job.status = "partial_failure"
            else:
                job.status = "failed"
                job.error = "All videos in batch failed to process"
            await session.commit()

    # Requirement 7: After videos finish, update twin store per zone and run risk evaluation
    now = time.time()
    for sz in successful_zones:
        code = sz["zone_code"]
        zid = zone_id_map.get(code)
        if not zid:
            continue
        count = sz["count"]
        density = sz["density"]
        mean_speed = sz.get("mean_speed", 1.0)
        opposing = sz.get("opposing_flow", 0.0)
        congestion = sz.get("congestion_index", 0.0)
        exit_pressure = min(2.0, density / 3.0 + opposing * 0.5 + congestion * 0.4)

        metrics = ZoneMetrics(
            zone_id=UUID(zid),
            timestamp=now,
            count=count,
            density=density,
            mean_speed=mean_speed,
            opposing_flow=opposing,
            group_cohesion=0.0,
            abnormal_motion=0.0,
            exit_pressure=round(exit_pressure, 3),
            weather_factor=0.0,
            time_prior=0.5,
            historical_hotspot=0.2 if code != "B" else 0.45,
            emergency_flag=0.0,
            forecast_surge=max(congestion, min(1.5, density / 4.0)),
        )
        twin_store.set_zone_metrics(zid, metrics)

    # Evaluate venue risk across all scored zones and produce recommendations
    risk_uc = EvaluateVenueRiskUseCase()
    risk_uc.execute(clear_alerts=True)
    logger.info(
        "Batch job %s complete: %d ok, %d failed. Monitored zones updated.",
        batch_id,
        completed_count,
        failed_count,
    )
