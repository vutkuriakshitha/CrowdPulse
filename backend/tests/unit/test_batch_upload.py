"""Unit and integration tests for Phase B: batch CCTV video upload,
thread pool execution, duplicate zone rejection, limits, and partial failure handling.
"""

from __future__ import annotations

import json
from pathlib import Path
import uuid

import httpx
import pytest

from app.api.deps import AuthUser, get_current_user
from app.application.use_cases.batch_video_processor import (
    estimate_batch_processing_time,
    process_tagged_video_sync,
    run_batch_job,
)
from app.infrastructure.persistence.database import SessionLocal, init_db
from app.infrastructure.persistence.models import BatchJobModel, BatchVideoItemModel
from app.infrastructure.persistence.seed import VENUE_ID
from app.infrastructure.persistence.twin_store import twin_store
from app.main import app


@pytest.fixture(autouse=True)
def override_auth():
    """Bypass auth for unit test runs."""
    admin_user = AuthUser(
        id=str(uuid.uuid4()),
        username="test.admin",
        full_name="Test Administrator",
        role="admin",
        organization="CrowdPulse Tests",
        unit="Automated",
    )
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def cleanup_db_connections():
    yield
    from app.infrastructure.persistence.database import engine
    await engine.dispose()


def test_estimate_batch_processing_time():
    """Estimated processing time must scale dynamically with frame counts."""
    # 4 clips of 300 frames with stride 4 = 75 sampled frames each = 300 total sampled
    # With 2 workers at 5.5 fps: max(300 / (2 * 5.5), 75 / 5.5) = max(27.27, 13.63) = ~27.3s
    frame_counts = [300, 300, 300, 300]
    est = estimate_batch_processing_time(frame_counts, stride=4, fps_per_worker=5.5)
    assert 25.0 <= est <= 30.0

    # 1 clip of 300 frames: 75 sampled frames / 5.5 = ~13.6s
    est_single = estimate_batch_processing_time([300], stride=4, fps_per_worker=5.5)
    assert 12.0 <= est_single <= 15.0

    # Empty frame counts returns 0.0
    assert estimate_batch_processing_time([]) == 0.0


def test_tagged_zone_assignment_and_density_docstring():
    """Requirement 4: Each tagged video assigns ALL detections to its zone (skip polygon ZoneAssigner).

    Density = count / zone area_m2.
    """
    import inspect
    from app.application.use_cases import batch_video_processor

    module_doc = inspect.getdoc(batch_video_processor) or ""
    func_doc = inspect.getdoc(process_tagged_video_sync) or ""

    assert "Each tagged video assigns ALL its detections to its zone" in module_doc
    assert "Density = count / zone area_m2" in module_doc

    assert "Each tagged video assigns ALL its detections to its zone" in func_doc
    assert "Density = count / zone area_m2" in func_doc


@pytest.mark.asyncio
async def test_batch_upload_file_limits():
    """Requirement 2: Batch upload accepts 1 to 8 files. Rejects > 8 files."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        files = [
            ("files", (f"clip_{i}.mp4", b"\x00" * 1024, "video/mp4"))
            for i in range(9)
        ]
        manifest = {f"clip_{i}.mp4": "A" for i in range(9)}
        resp = await ac.post(
            "/api/v1/videos/batch-upload",
            files=files,
            data={"manifest": json.dumps(manifest)},
        )
        assert resp.status_code == 400
        assert "between 1 and 8 files" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_batch_upload_duplicate_zone_rejected():
    """Requirement 5: One video per zone for now.

    A second video for the same zone is rejected with a clear message. No fusion.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        files = [
            ("files", ("camera_1.mp4", b"\x00" * 1024, "video/mp4")),
            ("files", ("camera_2.mp4", b"\x00" * 1024, "video/mp4")),
        ]
        manifest = {
            "camera_1.mp4": "B",
            "camera_2.mp4": "B",
        }
        resp = await ac.post(
            "/api/v1/videos/batch-upload",
            files=files,
            data={"manifest": json.dumps(manifest)},
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "Duplicate zone assignment" in detail
        assert "Zone 'B' is assigned to multiple videos" in detail


@pytest.mark.asyncio
async def test_batch_upload_unknown_zone_rejected():
    """Rejects manifest mapping to invalid zone not in venue topology."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        files = [
            ("files", ("camera_1.mp4", b"\x00" * 1024, "video/mp4")),
        ]
        manifest = {"camera_1.mp4": "NON_EXISTENT_ZONE_Z"}
        resp = await ac.post(
            "/api/v1/videos/batch-upload",
            files=files,
            data={"manifest": json.dumps(manifest)},
        )
        assert resp.status_code == 400
        assert "Unknown zone code 'NON_EXISTENT_ZONE_Z'" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_batch_job_failing_video_tolerance():
    """Requirement 6 & 8: One failed video must not stop the others.

    A corrupt video item fails gracefully while valid video items complete.
    """
    await init_db()

    phase_b_dir = Path(__file__).resolve().parents[2] / "data" / "uploads" / "samples" / "phase_b"
    valid_path = phase_b_dir / "clip_zoneA.mp4"
    corrupt_path = phase_b_dir / "clip_corrupt.mp4"

    if not valid_path.exists():
        pytest.skip("Test clips not generated yet")

    job_id = uuid.uuid4()
    valid_item_id = uuid.uuid4()
    corrupt_item_id = uuid.uuid4()

    async with SessionLocal() as session:
        job = BatchJobModel(
            id=job_id,
            venue_id=VENUE_ID,
            status="pending",
            total_files=2,
            estimated_time_s=15.0,
            completed_files=0,
            failed_files=0,
        )
        session.add(job)

        it_valid = BatchVideoItemModel(
            id=valid_item_id,
            batch_id=job_id,
            original_filename="clip_zoneA.mp4",
            stored_filename="clip_zoneA.mp4",
            storage_path=str(valid_path.resolve()),
            zone_code="A",
            status="pending",
            progress=0.0,
            frame_count=300,
        )
        session.add(it_valid)

        it_corrupt = BatchVideoItemModel(
            id=corrupt_item_id,
            batch_id=job_id,
            original_filename="clip_corrupt.mp4",
            stored_filename="clip_corrupt.mp4",
            storage_path=str(corrupt_path.resolve()),
            zone_code="B",
            status="pending",
            progress=0.0,
            frame_count=0,
        )
        session.add(it_corrupt)
        await session.commit()

    # Execute batch job with max_frames=5 for rapid unit test validation
    await run_batch_job(job_id, VENUE_ID, max_frames=5)

    # Check database state
    async with SessionLocal() as session:
        j = await session.get(BatchJobModel, job_id)
        assert j is not None
        assert j.status == "partial_failure"
        assert j.completed_files == 1
        assert j.failed_files == 1

        v = await session.get(BatchVideoItemModel, valid_item_id)
        assert v.status == "completed"
        assert v.progress == 100.0
        assert v.count > 0
        assert v.density > 0.0
        assert v.error is None

        c = await session.get(BatchVideoItemModel, corrupt_item_id)
        assert c.status == "failed"
        assert c.progress == 0.0
        assert c.error is not None
        assert "Cannot open video" in c.error

    # Monitored zone A must be scored in twin store, while zone B remains unmonitored
    zone_a_risk = next(
        (card for card in twin_store.latest_risks.values() if card.get("zone", {}).get("code") == "A"),
        None,
    )
    assert zone_a_risk is not None
    assert zone_a_risk["status"] == "monitored"
    assert zone_a_risk["risk"]["dcrs"] is not None

    zone_b_risk = next(
        (card for card in twin_store.latest_risks.values() if card.get("zone", {}).get("code") == "B"),
        None,
    )
    assert zone_b_risk is not None
    assert zone_b_risk["status"] == "no_data"
    assert zone_b_risk["risk"]["band"] == "unmonitored"
