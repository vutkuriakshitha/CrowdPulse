"""One-click Level A pipeline API."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthUser, require_operator
from app.application.use_cases.run_pipeline import PipelineRunRequest, RunPipelineUseCase
from app.core.config import settings
from app.infrastructure.persistence.database import get_db

router = APIRouter()


@router.post("/run")
async def run_pipeline(
    body: PipelineRunRequest = Body(default_factory=PipelineRunRequest),
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_operator),
):
    """Run full pipeline: video → detect → track → analytics → DCRS → ERA → GB → twin.

    Omit `video_id` to auto-use `synthetic_crowd.mp4` (generated if missing).
    """
    try:
        return await RunPipelineUseCase(db).execute(body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc


@router.get("/status")
async def pipeline_status():
    return {
        "endpoint": "POST /api/v1/pipeline/run",
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
        "defaults": {
            "sample_filename": "synthetic_crowd.mp4",
            "frame_stride": settings.demo_frame_stride,
            "max_frames": settings.demo_max_frames,
            "yolo_model": settings.yolo_model_name,
            "yolo_imgsz": settings.yolo_imgsz,
        },
    }
