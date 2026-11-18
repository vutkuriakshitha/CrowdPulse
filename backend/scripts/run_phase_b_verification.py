"""Comprehensive Phase B Live Verification Script for CrowdPulse.

Verifications:
1. Run a batch of 1 clip (clip_zoneA.mp4 -> Zone A).
2. Run a batch of 3 clips (clip_zoneA -> A, clip_zoneB -> B, clip_zoneC -> C).
3. Run a batch of 4 clips (clip_zoneA -> A, clip_zoneB -> B, clip_zoneC -> C, clip_zoneD -> D)
   while concurrently polling /system/health to measure response times and prove API responsiveness.
4. Run a batch with 1 corrupt clip and 1 valid clip to verify failure tolerance.
5. Report for each run: measured seconds, per-zone count, DCRS, band, and recommendations.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import subprocess
import sys
import time

sys.stdout.reconfigure(line_buffering=True)

import httpx

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

SAMPLES_DIR = BACKEND_DIR / "data" / "uploads" / "samples" / "phase_b"
BASE_URL = "http://127.0.0.1:8000"


async def wait_for_server(client: httpx.AsyncClient, max_retries: int = 30) -> bool:
    for _ in range(max_retries):
        try:
            r = await client.get(f"{BASE_URL}/health", timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return False


async def login(client: httpx.AsyncClient) -> str:
    res = await client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "tsp.admin", "password": "Admin@TS2026"},
    )
    if res.status_code != 200:
        raise RuntimeError(f"Login failed: {res.status_code} {res.text}")
    return res.json()["access_token"]


async def run_batch_test(
    client: httpx.AsyncClient,
    token: str,
    clips: list[tuple[str, str]],
    test_name: str,
    monitor_health: bool = False,
):
    print("=" * 80)
    print(f"VERIFICATION: {test_name}")
    print("=" * 80)

    # 1. Prepare files and manifest
    files = []
    manifest = {}
    opened_files = []

    try:
        for fname, zone in clips:
            fpath = SAMPLES_DIR / fname
            if not fpath.exists():
                raise FileNotFoundError(f"Sample clip not found: {fpath}")
            fh = open(fpath, "rb")
            opened_files.append(fh)
            files.append(("files", (fname, fh, "video/mp4")))
            manifest[fname] = zone

        headers = {"Authorization": f"Bearer {token}"}
        print(f"Uploading batch of {len(clips)} files: {manifest}")

        t_upload_start = time.time()
        res = await client.post(
            f"{BASE_URL}/api/v1/videos/batch-upload",
            files=files,
            data={"manifest": json.dumps(manifest)},
            headers=headers,
            timeout=30.0,
        )
        upload_time = time.time() - t_upload_start

        if res.status_code != 200:
            print(f"Upload failed: {res.status_code} {res.text}")
            return None

        body = res.json()
        batch_id = body["batch_id"]
        est_time = body.get("estimated_time_s", 0.0)
        print(f"Batch registered: ID={batch_id} | Estimated Time={est_time:.1f}s | Upload time={upload_time:.2f}s")

        # 2. Poll status until complete
        t_process_start = time.time()
        health_latencies: list[dict] = []
        last_poll_time = time.time()

        while True:
            # If monitoring health, ping /system/health
            if monitor_health and (time.time() - last_poll_time >= 1.0):
                t_h0 = time.time()
                try:
                    h_resp = await client.get(f"{BASE_URL}/system/health", timeout=3.0)
                    h_latency_ms = (time.time() - t_h0) * 1000.0
                    health_latencies.append({
                        "elapsed_s": round(time.time() - t_process_start, 2),
                        "status": h_resp.status_code,
                        "latency_ms": round(h_latency_ms, 2),
                    })
                except Exception as exc:
                    health_latencies.append({
                        "elapsed_s": round(time.time() - t_process_start, 2),
                        "status": "ERROR",
                        "error": str(exc),
                    })
                last_poll_time = time.time()

            try:
                status_res = await client.get(
                    f"{BASE_URL}/api/v1/videos/batch-jobs/{batch_id}",
                    headers=headers,
                    timeout=30.0,
                )
                if status_res.status_code == 200:
                    job = status_res.json()
                    status = job.get("status")
                    if status in {"completed", "failed", "partial_failure"}:
                        break
            except Exception as poll_exc:
                print(f"  [polling wait... {poll_exc}]")

            await asyncio.sleep(1.0)

        measured_time = time.time() - t_process_start
        print(f"\nBatch finished with status: {status.upper()} in {measured_time:.2f}s (Estimated: {est_time:.1f}s)")
        print(f"Items summary: {job.get('completed_files', 0)} completed, {job.get('failed_files', 0)} failed.")

        # Print per-video item details
        print("\n--- Per-Video Item Execution ---")
        for it in job.get("items", []):
            print(f"  * File: {it['original_filename']} -> Zone {it['zone_code']} | Status: {it['status']} | Progress: {it['progress']:.0f}% | Count: {it['count']} | Density: {it['density']:.3f} p/m² | Error: {it.get('error')}")

        # If health monitoring was active, display health latency statistics
        if monitor_health and health_latencies:
            valid_latencies = [h["latency_ms"] for h in health_latencies if "latency_ms" in h]
            print("\n--- Concurrent /system/health Responsiveness During 4-Clip Batch ---")
            print(f"  Total Health Calls Made: {len(health_latencies)}")
            if valid_latencies:
                print(f"  Min Latency: {min(valid_latencies):.2f} ms")
                print(f"  Mean Latency: {sum(valid_latencies)/len(valid_latencies):.2f} ms")
                print(f"  Max Latency: {max(valid_latencies):.2f} ms")
                print("  Sample Latency Readings during YOLO inference:")
                for sample in health_latencies[:: max(1, len(health_latencies) // 6)]:
                    print(f"    At {sample['elapsed_s']}s: Status {sample['status']} | Response Time: {sample.get('latency_ms')} ms")

        # 3. Fetch Twin Snapshot
        snap_res = await client.get(f"{BASE_URL}/api/v1/twin/snapshot", headers=headers, timeout=10.0)
        snap = snap_res.json()

        print("\n--- Digital Twin Per-Zone Status & Risk Scoring ---")
        for z in snap.get("zones", []):
            z_info = z.get("zone", {})
            z_code = z_info.get("code")
            status = z.get("status")
            metrics = z.get("metrics")
            risk = z.get("risk", {})
            count = metrics.get("count") if metrics else "—"
            density = f"{metrics.get('density'):.3f}" if metrics else "—"
            dcrs = f"{risk.get('dcrs'):.1f}" if risk.get("dcrs") is not None else "—"
            band = risk.get("band", "unmonitored").upper()
            print(f"  * Zone {z_code} ({z_info.get('name')}): Status={status.upper()} | Count={count} | Density={density} | DCRS={dcrs} | Band={band}")

        # Recommendations
        alerts = snap.get("alerts", [])
        print("\n--- Generated Cognitive Recommendations ---")
        if alerts:
            for al in alerts:
                print(f"  * Alert for Zone {al.get('zone_code')} (DCRS {al.get('dcrs', 0):.1f} - {al.get('band', '').upper()}):")
                print(f"    Rationale: {al.get('rationale')}")
                for ac in al.get("actions", []):
                    conf_pct = int(ac.get("confidence", 0.0) * 100)
                    print(f"      -> [{ac.get('action_type')}] {ac.get('title')} (score: {conf_pct}%) - {ac.get('description')}")
        else:
            print("  (All monitored zones within calm/monitored threshold; no emergency interventions triggered)")

        print("\n")
        return job

    finally:
        for fh in opened_files:
            fh.close()


async def main():
    print("Launching Uvicorn server for live Phase B batch verification...")
    log_path = BACKEND_DIR / "data" / "uvicorn_test.log"
    uvicorn_log = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "info",
        ],
        cwd=str(BACKEND_DIR),
        stdout=uvicorn_log,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        async with httpx.AsyncClient() as client:
            print("Waiting for server startup on http://127.0.0.1:8000...")
            if not await wait_for_server(client):
                print("Failed to reach CrowdPulse server within timeout.")
                return

            print("Server is healthy! Authenticating as tsp.admin...")
            token = await login(client)
            print("Authenticated successfully.")

            # Test 1: Single clip (Zone A)
            await run_batch_test(
                client=client,
                token=token,
                clips=[("clip_zoneA.mp4", "A")],
                test_name="Test 1: Single Clip Batch (Zone A)",
            )

            # Test 2: 3 Clips (Zones A, B, C)
            await run_batch_test(
                client=client,
                token=token,
                clips=[
                    ("clip_zoneA.mp4", "A"),
                    ("clip_zoneB.mp4", "B"),
                    ("clip_zoneC.mp4", "C"),
                ],
                test_name="Test 2: 3-Clip Batch (Zones A, B, C)",
            )

            # Test 3: 4 Clips (Zones A, B, C, D) + Concurrent /system/health Polling
            await run_batch_test(
                client=client,
                token=token,
                clips=[
                    ("clip_zoneA.mp4", "A"),
                    ("clip_zoneB.mp4", "B"),
                    ("clip_zoneC.mp4", "C"),
                    ("clip_zoneD.mp4", "D"),
                ],
                test_name="Test 3: 4-Clip Batch (Zones A, B, C, D) with Concurrent API Health Monitoring",
                monitor_health=True,
            )

            # Test 4: Corrupt File Batch (Failing video tolerance)
            await run_batch_test(
                client=client,
                token=token,
                clips=[
                    ("clip_corrupt.mp4", "B"),
                    ("clip_zoneA.mp4", "A"),
                ],
                test_name="Test 4: Failing Video Tolerance (Corrupt Clip + Valid Clip)",
            )

    finally:
        print("Shutting down uvicorn test process...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        finally:
            uvicorn_log.close()
        print("Uvicorn process cleanly terminated.")


if __name__ == "__main__":
    asyncio.run(main())
