"""Day 21 verify — demo pipeline finishes under 2 minutes; models cached."""

from __future__ import annotations

import sys
import time
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, get_json, post_json, public_get  # noqa: E402

ensure_login()

TARGET_MS = 120_000  # 2 minutes


def main() -> int:
    _, health = public_get("/health")
    assert health.get("status") == "ok"

    status = get_json("/api/v1/pipeline/status")
    defaults = status.get("defaults") or {}
    assert defaults.get("frame_stride", 0) >= 5
    assert defaults.get("max_frames", 999) <= 40
    print(
        f"[PASS] demo defaults stride={defaults.get('frame_stride')} "
        f"max_frames={defaults.get('max_frames')} "
        f"yolo={defaults.get('yolo_model')} imgsz={defaults.get('yolo_imgsz')}"
    )

    det = get_json("/api/v1/videos/detector/status")
    assert "engine" in det and "backend" in det
    print(f"[PASS] detector cached/warm engine={det.get('backend')}/{det.get('engine')}")

    rec = get_json("/api/v1/decisions/recommender/status")
    assert rec.get("fitted") is True, rec
    assert "GradientBoosting" in str(rec.get("algorithm", ""))
    print(f"[PASS] recommender fitted algorithm={rec.get('algorithm')}")

    t0 = time.perf_counter()
    pipe = post_json(
        "/api/v1/pipeline/run",
        {
            "sample_filename": "dense_crowd.mp4",
            "include_twin": True,
            # omit stride/max to use server demo defaults
        },
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert pipe.get("ok") is True
    reported = float(pipe.get("elapsed_ms") or elapsed_ms)
    assert reported < TARGET_MS, f"too slow: {reported}ms"
    assert elapsed_ms < TARGET_MS, f"wall clock too slow: {elapsed_ms}ms"
    print(
        f"[PASS] dense demo pipeline reported={reported:.0f}ms wall={elapsed_ms:.0f}ms "
        f"(target < {TARGET_MS}ms) peak={pipe.get('peak_zone')}:{pipe.get('peak_band')}"
    )
    print("Day 21 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
