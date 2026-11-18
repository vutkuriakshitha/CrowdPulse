"""End-to-End Verification Suite for Step 1 and Step 2 of CrowdPulse.

Step 1: Auth, Database, Configuration & Deployment Resilience
Step 2: Video Ingestion & Processing (Real CCTV Pedestrian Footage)
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from uuid import UUID

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import cv2
import numpy as np
from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.infrastructure.persistence.database import SessionLocal, init_db
from app.infrastructure.persistence.models import (
    CameraModel,
    DetectionRunModel,
    UserModel,
    VenueModel,
    VideoAssetModel,
    ZoneModel,
)
from app.infrastructure.persistence.repository import venue_to_dict
from app.infrastructure.persistence.seed import CONTROL_ROOM_USERS, get_demo_venue
from app.infrastructure.persistence.twin_store import twin_store
from app.infrastructure.storage.video_storage import LocalVideoStorage
from app.ai.perception.detector import get_person_detector
from app.ai.perception.tracker import CentroidTracker
from app.ai.perception.video_processor import process_video_file
from app.application.use_cases.process_video import ProcessVideoUseCase
from app.application.use_cases.run_pipeline import PipelineRunRequest, RunPipelineUseCase


class VerificationResult:
    def __init__(self, step_name: str):
        self.step_name = step_name
        self.tests: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, details: str = "") -> bool:
        status_str = "PASS" if condition else "FAIL"
        print(f"  [{status_str}] {name} {f'({details})' if details else ''}", flush=True)
        self.tests.append((name, condition, details))
        return condition

    @property
    def passed(self) -> int:
        return sum(1 for _, ok, _ in self.tests if ok)

    @property
    def total(self) -> int:
        return len(self.tests)

    @property
    def all_ok(self) -> bool:
        return all(ok for _, ok, _ in self.tests)


async def verify_step_1() -> VerificationResult:
    print("\n" + "=" * 70, flush=True)
    print("  VERIFYING STEP 1: AUTH, DATABASE, CONFIGURATION & DEPLOYMENT", flush=True)
    print("=" * 70, flush=True)
    res = VerificationResult("Step 1: Auth, DB & Deployment Resilience")

    # 1.1 Database Initialization
    await init_db()
    res.check("Database Schema Initialized", True, f"SQLite DB: {settings.database_url}")

    async with SessionLocal() as db:
        # 1.2 Seeded Users
        users = (await db.execute(select(UserModel))).scalars().all()
        user_map = {u.username: u for u in users}
        res.check(
            "Control-Room Seeded Users Present",
            "tsp.operator" in user_map and "tsp.admin" in user_map and "stadium.ops" in user_map,
            f"Found {len(users)} users: {list(user_map.keys())}",
        )

        # 1.3 User Roles & Verification
        op_user = user_map.get("tsp.operator")
        admin_user = user_map.get("tsp.admin")
        res.check(
            "User Roles Assigned Correctly",
            op_user is not None and op_user.role == "operator" and admin_user is not None and admin_user.role == "admin",
            f"tsp.operator: role={op_user.role if op_user else 'None'}, tsp.admin: role={admin_user.role if admin_user else 'None'}",
        )

        # 1.4 Password Hashing & Verification
        raw_pw = "Operator@TS2026"
        pw_ok = verify_password(raw_pw, op_user.password_hash) if op_user else False
        res.check("Bcrypt Password Hash Verification", pw_ok, "Verified Operator@TS2026 matches stored bcrypt hash")

        bad_pw_rejected = not verify_password("WrongPassword123", op_user.password_hash) if op_user else False
        res.check("Invalid Password Rejection", bad_pw_rejected, "Confirmed wrong password fails verification")

        # 1.5 JWT Lifecycle & Token Claims
        token = create_access_token(
            subject="tsp.operator",
            role="operator",
            full_name="Control Room Operator",
            organization="Telangana State Police",
            unit="Integrated Command Control Centre (ICCC)",
            expires_minutes=480,
        )
        claims = decode_access_token(token)
        jwt_ok = (
            claims.get("sub") == "tsp.operator"
            and claims.get("role") == "operator"
            and claims.get("iss") == "crowdpulse"
            and "exp" in claims
        )
        res.check("JWT Token Lifecycle & Claims", jwt_ok, f"Subject={claims.get('sub')}, Issuer={claims.get('iss')}, Role={claims.get('role')}")

        # 1.6 Venue & Topology Initialization
        venue = await get_demo_venue(db)
        venue_ok = venue is not None and len(venue.zones) == 4 and len(venue.cameras) == 3
        res.check(
            "Venue & Zone Topology Seeded",
            venue_ok,
            f"Venue: {venue.name if venue else 'None'}, Zones={len(venue.zones) if venue else 0}, Cameras={len(venue.cameras) if venue else 0}",
        )

    # 1.7 FastAPI App & Health Routes via AsyncClient
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Public Root /
        r_root = await client.get("/")
        # Note: root redirects or health
        r_health = await client.get("/health")
        h_data = r_health.json() if r_health.status_code == 200 else {}
        res.check(
            "Public /health Probe Accessible",
            r_health.status_code == 200 and h_data.get("status") == "ok" and h_data.get("database", {}).get("ok") is True,
            f"Status={r_health.status_code}, DB Venues={h_data.get('database', {}).get('venues')}",
        )

        # Public API Health /api/v1/health
        r_v1_health = await client.get("/api/v1/health")
        v1_h_data = r_v1_health.json() if r_v1_health.status_code == 200 else {}
        res.check(
            "Public /api/v1/health Probe Accessible",
            r_v1_health.status_code == 200 and v1_h_data.get("status") == "ok",
            f"Status={r_v1_health.status_code}, Service={v1_h_data.get('service')}",
        )

        # API v1 Root Catalog
        r_v1_root = await client.get("/api/v1/")
        res.check(
            "Public /api/v1/ Root Module Catalog Accessible",
            r_v1_root.status_code == 200 and "modules" in r_v1_root.json(),
            f"Status={r_v1_root.status_code}, Modules={len(r_v1_root.json().get('modules', []))}",
        )

        # Login Endpoint (Valid)
        r_login = await client.post(
            "/api/v1/auth/login",
            json={"username": "tsp.operator", "password": "Operator@TS2026"},
        )
        login_data = r_login.json() if r_login.status_code == 200 else {}
        has_token = r_login.status_code == 200 and "access_token" in login_data
        res.check(
            "Authentication Endpoint POST /api/v1/auth/login",
            has_token,
            f"Status={r_login.status_code}, User={login_data.get('user', {}).get('username')}, Role={login_data.get('user', {}).get('role')}",
        )

        # Login Endpoint (Invalid)
        r_bad_login = await client.post(
            "/api/v1/auth/login",
            json={"username": "tsp.operator", "password": "WrongPassword!"},
        )
        res.check(
            "Invalid Login HTTP 401 Rejection",
            r_bad_login.status_code == 401,
            f"Status={r_bad_login.status_code}, Detail={r_bad_login.json().get('detail')}",
        )

        # Protected Endpoint Verification
        if has_token:
            auth_header = {"Authorization": f"Bearer {login_data['access_token']}"}
            # Unauthenticated access to /api/v1/venues/ should be 401
            r_unauth_venues = await client.get("/api/v1/venues/", follow_redirects=True)
            res.check(
                "Protected Endpoint Rejects Unauthenticated Request",
                r_unauth_venues.status_code == 401,
                f"Status={r_unauth_venues.status_code}",
            )

            # Authenticated access to /api/v1/auth/me
            r_me = await client.get("/api/v1/auth/me", headers=auth_header)
            me_ok = r_me.status_code == 200 and r_me.json().get("username") == "tsp.operator"
            res.check(
                "Authenticated GET /api/v1/auth/me Verification",
                me_ok,
                f"Status={r_me.status_code}, User={r_me.json().get('full_name')}",
            )

            # Authenticated access to /api/v1/venues/
            r_venues = await client.get("/api/v1/venues/", headers=auth_header, follow_redirects=True)
            res.check(
                "Authenticated GET /api/v1/venues/ Access",
                r_venues.status_code == 200 and len(r_venues.json()) > 0,
                f"Status={r_venues.status_code}, Venues Found={len(r_venues.json())}",
            )

    # 1.8 CORS Configuration
    res.check(
        "CORS Origins Configured for Development and Production",
        "http://localhost:3000" in settings.cors_origins and "http://127.0.0.1:3000" in settings.cors_origins,
        f"Allowed origins: {len(settings.cors_origins)} origins configured",
    )

    return res


async def verify_step_2() -> VerificationResult:
    print("\n" + "=" * 70, flush=True)
    print("  VERIFYING STEP 2: VIDEO INGESTION & PROCESSING (REAL CCTV FOOTAGE)", flush=True)
    print("=" * 70, flush=True)
    res = VerificationResult("Step 2: Video Ingestion & Processing")

    samples_dir = BACKEND_DIR / "data" / "uploads" / "samples"
    res.check("Samples Directory Exists", samples_dir.exists(), str(samples_dir))

    # 2.1 Sample Clips Validation (Authorized CUHK Mall Dataset Footage)
    sample_files = ["sparse_crowd.mp4", "medium_crowd.mp4", "dense_crowd.mp4", "mall_dataset.mp4"]
    for fname in sample_files:
        p = samples_dir / fname
        if not p.exists():
            res.check(f"Sample Video Exists: {fname}", False, "File missing on disk")
            continue

        cap = cv2.VideoCapture(str(p))
        is_open = cap.isOpened()
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        cap.release()

        valid_cctv = is_open and fps > 0 and w >= 320 and h >= 240 and frames > 10
        res.check(
            f"Real CCTV Video Integrity: {fname}",
            valid_cctv,
            f"Size={p.stat().st_size / 1024 / 1024:.2f} MB, {w}x{h} @ {fps:.1f}fps, {frames} frames",
        )

    # 2.2 Storage System Validation
    storage = LocalVideoStorage()
    res.check(
        "Local Video Storage Directory Initialized",
        Path(storage.root).exists(),
        f"Storage Root: {storage.root}",
    )

    # 2.3 Real Pedestrian Detection on CCTV Frame (YOLOv8n)
    t0 = time.perf_counter()
    detector = get_person_detector()
    load_time = time.perf_counter() - t0
    res.check(
        "Real Pedestrian Detector Loaded (YOLOv8n)",
        detector is not None and "yolo" in detector.info.backend,
        f"Engine: {detector.info.name} ({detector.info.backend}) loaded in {load_time:.2f}s",
    )

    # Extract 1 frame from sparse_crowd and 1 from dense_crowd
    sparse_cap = cv2.VideoCapture(str(samples_dir / "sparse_crowd.mp4"))
    ok_sparse, sparse_frame = sparse_cap.read()
    sparse_cap.release()

    dense_cap = cv2.VideoCapture(str(samples_dir / "dense_crowd.mp4"))
    ok_dense, dense_frame = dense_cap.read()
    dense_cap.release()

    res.check("CCTV Frame Read via OpenCV", ok_sparse and ok_dense, f"Sparse shape: {sparse_frame.shape if ok_sparse else 'None'}")

    if ok_sparse and ok_dense:
        t_inf0 = time.perf_counter()
        dets_sparse = detector.detect(sparse_frame)
        t_sparse = time.perf_counter() - t_inf0

        dets_dense = detector.detect(dense_frame)
        res.check(
            "Pedestrian Detections on Real CCTV Footage",
            len(dets_sparse) > 0 and len(dets_dense) > len(dets_sparse),
            f"Sparse count={len(dets_sparse)} in {t_sparse:.2f}s | Dense count={len(dets_dense)} (Real CCTV differentiation proven)",
        )

        # Validate bounding box attributes
        sample_det = dets_sparse[0]
        valid_bbox = (
            len(sample_det.bbox) == 4
            and sample_det.bbox[2] > sample_det.bbox[0]
            and sample_det.bbox[3] > sample_det.bbox[1]
            and 0.0 <= sample_det.confidence <= 1.0
        )
        res.check(
            "Bounding Box Geometry & Confidence Validity",
            valid_bbox,
            f"BBox: {[round(c, 1) for c in sample_det.bbox]}, Conf: {sample_det.confidence:.2f}, Class: {sample_det.class_name}",
        )

    # 2.4 Multi-Object Tracking (CentroidTracker)
    tracker = CentroidTracker(max_lost=10, dist_threshold=80.0)
    tracks_f1 = tracker.update(dets_sparse)
    tracks_f2 = tracker.update(dets_sparse)
    res.check(
        "Centroid Tracking Across Video Frames",
        len(tracks_f1) > 0 and all(t.track_id is not None for t in tracks_f1),
        f"Frame 1 tracks={len(tracks_f1)}, Frame 2 tracks={len(tracks_f2)}",
    )

    # 2.5 H.264 Video Transcoding Verification (Browser Compatibility)
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    res.check("imageio-ffmpeg H.264 Transcoder Available", Path(ffmpeg_exe).exists(), f"FFmpeg: {Path(ffmpeg_exe).name}")

    # 2.6 Full End-to-End Pipeline Execution on Real CCTV Footage
    print("  Executing End-to-End Pipeline on real CCTV clip (sparse_crowd.mp4)...", flush=True)
    async with SessionLocal() as session:
        venue = await get_demo_venue(session)
        twin_store.load_venue(venue_to_dict(venue, include_cameras=True))

        req = PipelineRunRequest(
            sample_filename="sparse_crowd.mp4",
            frame_stride=12,
            max_frames=6,
            include_twin=True,
        )
        t_pipe0 = time.perf_counter()
        pipeline_res = await RunPipelineUseCase(session).execute(req)
        pipe_elapsed = time.perf_counter() - t_pipe0

        stages = [s.get("name") for s in pipeline_res.get("stages", [])]
        expected_stages = ["resolve_video", "detect_track_analytics", "dcrs_era_recommend", "twin_snapshot"]
        res.check(
            "Pipeline Multi-Stage Execution Complete",
            all(s in stages for s in expected_stages),
            f"Executed in {pipe_elapsed:.1f}s, Stages: {stages}",
        )

        summary = pipeline_res.get("summary") or {}
        res.check(
            "Video Analytics Metrics Extracted from Real CCTV",
            summary.get("max_count", 0) > 0 and summary.get("unique_tracks", 0) > 0,
            f"Max Count: {summary.get('max_count')}, Unique Tracks: {summary.get('unique_tracks')}, Frames: {summary.get('frames_processed')}",
        )

        res.check(
            "DCRS Risk Score Computed for Video Analytics",
            pipeline_res.get("peak_dcrs") is not None and pipeline_res.get("peak_zone") is not None,
            f"Peak Zone={pipeline_res.get('peak_zone')}, Band={pipeline_res.get('peak_band')}, DCRS={pipeline_res.get('peak_dcrs')}",
        )

        annotated_url = pipeline_res.get("annotated_url")
        preview_url = pipeline_res.get("preview_url")
        res.check(
            "Proof-of-Detection Annotated Video & Thumbnail Generated",
            annotated_url is not None and preview_url is not None,
            f"Annotated URL: {annotated_url}, Preview URL: {preview_url}",
        )

        # Verify physical file existence of annotated MP4
        ann_path = summary.get("annotated_path")
        res.check(
            "Annotated Browser-Playable MP4 File on Disk",
            ann_path is not None and Path(ann_path).exists() and Path(ann_path).stat().st_size > 1000,
            f"File: {Path(ann_path).name if ann_path else 'None'} ({Path(ann_path).stat().st_size if ann_path and Path(ann_path).exists() else 0} bytes)",
        )

    return res


async def main():
    print("=" * 70, flush=True)
    print("  CROWDPULSE: SYSTEM VERIFICATION SUITE — STEP 1 & STEP 2", flush=True)
    print("  Telangana State Police & Stadium Operations Platform", flush=True)
    print("=" * 70, flush=True)

    r1 = await verify_step_1()
    r2 = await verify_step_2()

    print("\n" + "=" * 70, flush=True)
    print("  VERIFICATION SUMMARY REPORT", flush=True)
    print("=" * 70, flush=True)
    print(f"  Step 1 (Auth, DB & Deployment): {r1.passed}/{r1.total} tests passed ({'SUCCESS' if r1.all_ok else 'FAILED'})", flush=True)
    print(f"  Step 2 (Video Ingest & Processing): {r2.passed}/{r2.total} tests passed ({'SUCCESS' if r2.all_ok else 'FAILED'})", flush=True)
    print(f"  Total Step 1 & 2 Tests: {r1.passed + r2.passed}/{r1.total + r2.total} passed", flush=True)
    print("=" * 70 + "\n", flush=True)

    if not (r1.all_ok and r2.all_ok):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
