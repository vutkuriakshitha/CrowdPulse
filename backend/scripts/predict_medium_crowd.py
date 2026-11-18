"""Run medium-crowd.mp4 and print module-by-module expected UI outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, get_json, post_json  # noqa: E402

SAMPLE = "medium-crowd.mp4"


def main() -> int:
    ensure_login()
    det = get_json("/api/v1/videos/detector/status")
    print("=== DETECTOR STATUS ===")
    print(json.dumps(det, indent=2))

    print("\n=== RUNNING PIPELINE ===")
    r = post_json(
        "/api/v1/pipeline/run",
        {
            "sample_filename": SAMPLE,
            "frame_stride": 8,
            "max_frames": 24,
            "include_twin": True,
        },
    )
    assert r.get("ok") is True, r

    print("\n=== 1. VIDEO / RESOLVE ===")
    print(json.dumps(r.get("video"), indent=2, default=str))

    print("\n=== 2. DETECTION + TRACKING ===")
    print("engine:", r.get("engine"), "backend:", r.get("backend"), "tracker:", r.get("tracker"))
    print("summary:", json.dumps(r.get("summary"), indent=2, default=str))
    print("empty_detections:", r.get("empty_detections"), "warning:", r.get("warning"))

    print("\n=== 3. ZONE ANALYTICS ===")
    print(json.dumps(r.get("zone_summary"), indent=2, default=str))

    print("\n=== 4. DCRS RISK ===")
    print("peak_zone:", r.get("peak_zone"), "peak_band:", r.get("peak_band"), "peak_dcrs:", r.get("peak_dcrs"))
    print(json.dumps(r.get("risk_by_zone"), indent=2, default=str)[:4000])

    print("\n=== 5. ALERTS + GB ACTIONS ===")
    alerts = r.get("alerts") or []
    print("alert_count:", len(alerts))
    for a in alerts[:3]:
        print("--- alert", a.get("zone_code"), a.get("band"), a.get("dcrs"))
        print("explanation snippet:", str(a.get("explanation"))[:300])
        for act in (a.get("actions") or [])[:3]:
            print(
                "  action:",
                act.get("action_type"),
                "conf:",
                act.get("confidence"),
                "status:",
                act.get("status"),
            )

    print("\n=== 6. TWIN SNAPSHOT (UI map) ===")
    twin = r.get("twin") or get_json("/api/v1/twin/snapshot")
    for z in twin.get("zones") or []:
        code = (z.get("zone") or {}).get("code")
        m = z.get("metrics") or {}
        rk = z.get("risk") or {}
        print(
            f"zone {code}: count={m.get('count')} dens={m.get('density')} "
            f"speed={m.get('mean_speed')} dcrs={rk.get('dcrs')} band={rk.get('band')}"
        )
    print("twin_alerts:", len(twin.get("alerts") or []))

    print("\n=== STAGES ===")
    for s in r.get("stages") or []:
        print(s)

    out = Path(__file__).resolve().parents[1] / "data" / "demo_backup" / "medium_crowd_pipeline_result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, indent=2, default=str), encoding="utf-8")
    print("\nSaved:", out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
