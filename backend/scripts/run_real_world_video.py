"""Process the public real-world pedestrian clip through CrowdPulse pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, get_json, post_json  # noqa: E402

SAMPLE = "real_world_crowd.mp4"


def main() -> int:
    ensure_login()
    print(f"Running pipeline on {SAMPLE} (CPU may take 1–3 min)...")
    r = post_json(
        "/api/v1/pipeline/run",
        {
            "sample_filename": SAMPLE,
            "frame_stride": 4,
            "max_frames": 60,
            "include_twin": True,
        },
    )
    assert r.get("ok") is True, r
    print(
        f"[PASS] peak={r.get('peak_zone')}:{r.get('peak_band')} "
        f"DCRS={r.get('peak_dcrs')} elapsed={r.get('elapsed_ms')}ms"
    )
    print(f"[INFO] detection_engine={r.get('detection_engine') or r.get('engine')}")

    det = r.get("detection") or {}
    print(
        "[INFO] detection",
        {
            k: det.get(k)
            for k in (
                "engine",
                "frames_processed",
                "total_detections",
                "unique_tracks",
                "mean_count",
            )
            if det.get(k) is not None
        },
    )

    twin = get_json("/api/v1/twin/snapshot")
    print(f"[PASS] twin alerts={len(twin.get('alerts') or [])}")
    for z in twin.get("zones") or []:
        code = (z.get("zone") or {}).get("code") or z.get("zone_code")
        m = z.get("metrics") or {}
        rk = z.get("risk") or {}
        print(
            f"  zone {code}: count={m.get('count')} dens={m.get('density')} "
            f"dcrs={rk.get('dcrs')} band={rk.get('band')}"
        )
    print("Real-world video run OK — refresh the dashboard to see twin colors")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
