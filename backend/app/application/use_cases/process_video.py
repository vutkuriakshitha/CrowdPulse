"""Use-case: detect + track + zone-assign + DCRS risk from an uploaded CCTV video."""

from __future__ import annotations

import logging
import time
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.perception.video_processor import process_video_file, result_to_dict
from app.application.use_cases.evaluate_risk import EvaluateVenueRiskUseCase
from app.domain.entities.crowd import ZoneMetrics
from app.infrastructure.persistence.models import (
    AlertModel,
    DetectionRunModel,
    RiskSnapshotModel,
    VenueModel,
    VideoAssetModel,
)
from app.infrastructure.persistence.seed import VENUE_ID, get_demo_venue
from app.infrastructure.persistence.twin_store import twin_store

logger = logging.getLogger(__name__)


def camera_fov_density(count: int, area_m2: float) -> float:
    """Local density for single-camera Level A (no calibrated homography).

    Venue area_m2 is the full zone footprint; the camera only sees a share of it.
    We map that to an effective FOV area so count→density is usable for DCRS.
    """
    fov_m2 = max(6.0, min(float(area_m2) * 0.08, 20.0))
    return float(count) / fov_m2


class ProcessVideoUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _load_zones(self, venue_id: UUID | None) -> list[dict]:
        vid = venue_id or VENUE_ID
        result = await self.session.execute(
            select(VenueModel)
            .options(selectinload(VenueModel.zones))
            .where(VenueModel.id == vid)
        )
        venue = result.scalar_one_or_none()
        if not venue:
            venue = await get_demo_venue(self.session)
        if not venue:
            return []
        return [
            {
                "id": str(z.id),
                "code": z.code,
                "name": z.name,
                "polygon": z.polygon or [],
                "area_m2": z.area_m2,
            }
            for z in sorted(venue.zones, key=lambda x: x.code)
        ]

    def _push_zone_counts_to_twin(self, zone_summary: dict[str, dict]) -> None:
        """Update live twin metrics from video analytics (FOV-aware density for DCRS)."""
        now = time.time()
        code_to_zone = {z["code"]: z for z in twin_store.venue.get("zones", [])}
        for code, summary in zone_summary.items():
            z = code_to_zone.get(code)
            if not z:
                continue
            zid = z["id"]
            area = float(summary.get("area_m2") or z.get("area_m2") or 100.0)
            peak = int(max(summary.get("max_count") or 0, summary.get("latest_count") or 0))
            density = camera_fov_density(peak, area)
            mean_speed = float(summary.get("mean_speed") or 0.0)
            opposing = float(summary.get("opposing_flow") or 0.0)
            congestion = float(summary.get("congestion_index") or 0.0)
            # Recompute pressure proxies with FOV density so DCRS can escalate on dense clips
            exit_pressure = min(2.0, density / 3.0 + opposing * 0.5 + congestion * 0.4)
            abnormal = float(summary.get("abnormal_motion") or 0.0)
            if peak >= 4 and abnormal < 0.2:
                abnormal = min(1.0, 0.15 + peak * 0.04)
            twin_store.metrics[zid] = ZoneMetrics(
                zone_id=UUID(zid),
                timestamp=now,
                count=peak,
                density=round(density, 4),
                mean_speed=mean_speed,
                opposing_flow=opposing,
                group_cohesion=float(summary.get("group_cohesion") or 0.0),
                abnormal_motion=abnormal,
                exit_pressure=round(exit_pressure, 3),
                weather_factor=0.0,
                time_prior=0.5,
                historical_hotspot=0.2 if code != "B" else 0.45,
                emergency_flag=0.0,
                forecast_surge=max(congestion, min(1.5, density / 4.0)),
            )
            # Keep raw analytics density on summary for API transparency
            summary["risk_density"] = round(density, 4)
            summary["fov_area_m2"] = round(max(6.0, min(area * 0.08, 20.0)), 2)

    async def _persist_risk(
        self,
        risk_result: dict,
        *,
        video_id: UUID,
        run_id: UUID,
    ) -> None:
        for card in risk_result.get("zones", []):
            z = card["zone"]
            risk = card["risk"]
            self.session.add(
                RiskSnapshotModel(
                    id=uuid4(),
                    zone_id=UUID(z["id"]),
                    video_id=video_id,
                    detection_run_id=run_id,
                    dcrs=float(risk["dcrs"]),
                    band=str(risk["band"]),
                    metrics=card.get("metrics") or {},
                    features=card.get("features") or {},
                    explanation=card.get("explanation") or {},
                    source="video",
                )
            )
        for alert in risk_result.get("alerts", []):
            expl = alert.get("explanation")
            if isinstance(expl, str):
                expl_payload = {
                    "narrative": expl,
                    "actions": alert.get("actions"),
                    "rationale": alert.get("rationale"),
                }
            else:
                expl_payload = {
                    **(expl or {}),
                    "actions": alert.get("actions"),
                    "rationale": alert.get("rationale"),
                }
            self.session.add(
                AlertModel(
                    id=UUID(alert["id"]),
                    zone_id=UUID(alert["zone_id"]),
                    severity=alert.get("severity") or "warning",
                    status="open",
                    dcrs=float(alert["dcrs"]),
                    band=str(alert["band"]),
                    explanation=expl_payload,
                )
            )

    async def execute(
        self,
        video_id: UUID,
        *,
        frame_stride: int | None = None,
        max_frames: int | None = None,
    ) -> dict:
        import asyncio

        from app.core.config import settings

        frame_stride = frame_stride if frame_stride is not None else settings.demo_frame_stride
        max_frames = max_frames if max_frames is not None else settings.demo_max_frames

        row = await self.session.get(VideoAssetModel, video_id)
        if not row:
            raise FileNotFoundError("Video not found")

        # Fail fast on missing/empty storage before flipping status
        from pathlib import Path

        storage = Path(row.storage_path) if row.storage_path else None
        if not storage or not storage.exists():
            raise FileNotFoundError(f"Video file missing on disk: {row.original_filename}")
        if storage.stat().st_size <= 32:
            raise ValueError(f"Video file too small or empty: {row.original_filename}")

        row.status = "processing"
        await self.session.commit()
        venue_zones = await self._load_zones(row.venue_id)
        logger.info(
            "pipeline.stage=process_start video_id=%s file=%s stride=%s max_frames=%s",
            video_id,
            row.original_filename,
            frame_stride,
            max_frames,
        )

        try:
            ann_dir = Path(settings.video_upload_dir) / "annotated"
            ann_dir.mkdir(parents=True, exist_ok=True)
            annotated_out = ann_dir / f"{row.id}_annotated.mp4"
            preview_out = ann_dir / f"{row.id}_preview.jpg"

            result = await asyncio.to_thread(
                process_video_file,
                row.storage_path,
                frame_stride=frame_stride,
                max_frames=max_frames,
                venue_zones=venue_zones,
                annotated_out=annotated_out,
                preview_out=preview_out,
            )
            payload = result_to_dict(result)
            empty_detections = result.frames_processed == 0 or (
                result.max_count == 0 and result.unique_tracks == 0
            )
            annotated_url = f"/api/v1/videos/{row.id}/annotated" if result.annotated_path else None
            preview_url = f"/api/v1/videos/{row.id}/preview" if result.preview_path else None
            if empty_detections:
                logger.warning(
                    "pipeline.stage=detect_empty video_id=%s frames=%s — completing with zero counts",
                    video_id,
                    result.frames_processed,
                )
            self._push_zone_counts_to_twin(result.zone_summary)
            logger.info("pipeline.stage=dcrs_era_recommend video_id=%s", video_id)
            risk_result = EvaluateVenueRiskUseCase().execute(clear_alerts=True)

            risk_by_zone = {
                card["zone"]["code"]: {
                    "zone_id": card["zone"]["id"],
                    "dcrs": card["risk"]["dcrs"],
                    "band": card["risk"]["band"],
                    "count": card["metrics"].get("count"),
                    "density": card["metrics"].get("density"),
                    "mean_speed": card["metrics"].get("mean_speed"),
                    "opposing_flow": card["metrics"].get("opposing_flow"),
                    "exit_pressure": card["metrics"].get("exit_pressure"),
                    "explanation": (card.get("explanation") or {}).get("narrative"),
                    "why": {
                        "narrative": (card.get("explanation") or {}).get("narrative"),
                        "contributions": (card.get("explanation") or {}).get("contributions", [])[:5],
                    },
                }
                for card in risk_result.get("zones", [])
            }

            run = DetectionRunModel(
                id=uuid4(),
                video_id=row.id,
                engine=result.engine,
                backend=result.backend,
                status="completed",
                summary={
                    "max_count": result.max_count,
                    "avg_count": result.avg_count,
                    "frames_processed": result.frames_processed,
                    "fps": result.fps,
                    "duration_sec": result.duration_sec,
                    "unique_tracks": result.unique_tracks,
                    "tracker": result.tracker,
                    "sample_boxes": result.sample_boxes,
                    "zone_summary": result.zone_summary,
                    "zone_analytics": result.zone_analytics,
                    "risk_by_zone": risk_by_zone,
                    "peak_dcrs": risk_result.get("peak_dcrs"),
                    "peak_zone": risk_result.get("peak_zone"),
                    "peak_band": risk_result.get("peak_band"),
                    "annotated_path": result.annotated_path,
                    "preview_path": result.preview_path,
                    "annotated_url": annotated_url,
                    "preview_url": preview_url,
                },
                timeline=payload["timeline"],
            )
            self.session.add(run)
            await self.session.flush()
            await self._persist_risk(risk_result, video_id=row.id, run_id=run.id)

            peak = risk_result.get("peak_band")
            row.status = "completed"
            warn = " | empty_detections" if empty_detections else ""
            row.notes = (
                f"Analytics+DCRS via {result.backend}/{result.engine}+{result.tracker}. "
                f"tracks={result.unique_tracks}, max={result.max_count}, "
                f"peak={risk_result.get('peak_zone')}:{peak} "
                f"DCRS={risk_result.get('peak_dcrs')}{warn}"
            )
            await self.session.commit()
            await self.session.refresh(run)
            await self.session.refresh(row)
            logger.info(
                "pipeline.stage=process_done video_id=%s peak=%s:%s empty=%s annotated=%s",
                video_id,
                risk_result.get("peak_zone"),
                peak,
                empty_detections,
                bool(annotated_url),
            )
            return {
                "ok": True,
                "video": {
                    "id": str(row.id),
                    "status": row.status,
                    "original_filename": row.original_filename,
                },
                "run_id": str(run.id),
                "engine": run.engine,
                "backend": run.backend,
                "tracker": result.tracker,
                "summary": run.summary,
                "zone_summary": result.zone_summary,
                "zone_analytics": result.zone_analytics,
                "risk_by_zone": risk_by_zone,
                "peak_dcrs": risk_result.get("peak_dcrs"),
                "peak_zone": risk_result.get("peak_zone"),
                "peak_band": risk_result.get("peak_band"),
                "alerts": risk_result.get("alerts") or [],
                "timeline": run.timeline,
                "empty_detections": empty_detections,
                "annotated_url": annotated_url,
                "preview_url": preview_url,
                "warning": (
                    "No people detected in sampled frames. Twin updated with zero counts."
                    if empty_detections
                    else None
                ),
            }
        except (FileNotFoundError, ValueError):
            row.status = "failed"
            await self.session.commit()
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Detection/tracking/DCRS failed for %s", video_id)
            row.status = "failed"
            row.notes = f"Detection failed: {exc}"
            self.session.add(
                DetectionRunModel(
                    video_id=row.id,
                    engine="unknown",
                    backend="unknown",
                    status="failed",
                    summary={},
                    timeline=[],
                    error=str(exc),
                )
            )
            await self.session.commit()
            raise
