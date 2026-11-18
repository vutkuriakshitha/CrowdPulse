"""Day 23 verify — full Level A rehearsal (API demo script, no UI)."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from make_sample_pack import main as make_pack  # noqa: E402
from cp_http import ensure_login, get_json, post, post_json, public_get  # noqa: E402

ensure_login()


def main() -> int:
    make_pack()
    print("[PASS] sample pack ready")

    _, health = public_get("/health")
    assert health.get("status") == "ok"
    assert health.get("database", {}).get("ok") is True
    db_url_hint = "postgres" if "venues" in str(health.get("database")) else "db"
    print(f"[PASS] health ok database={health.get('database')} ({db_url_hint})")

    det = get_json("/api/v1/videos/detector/status")
    engine = (det.get("engine") or det.get("backend") or det.get("name") or "").lower()
    print(f"[INFO] detector status: {det}")
    # Prefer YOLO; HOG still passes rehearsal but flag it
    if "yolo" in engine or "ultralytics" in engine:
        print(f"[PASS] detector is YOLO ({engine})")
    else:
        print(f"[WARN] detector is not YOLO ({engine}) — restart uvicorn after ultralytics install")

    pipe = post_json(
        "/api/v1/pipeline/run",
        {
            "sample_filename": "dense_crowd.mp4",
            "frame_stride": 8,
            "max_frames": 24,
            "include_twin": True,
        },
    )
    assert pipe.get("ok") is True
    assert pipe.get("risk_by_zone")
    assert pipe.get("peak_band") in ("green", "yellow", "orange", "red")
    print(
        f"[PASS] dense pipeline peak={pipe.get('peak_zone')}:{pipe.get('peak_band')} "
        f"DCRS={pipe.get('peak_dcrs')} elapsed={pipe.get('elapsed_ms')}ms"
    )
    if pipe.get("detection_engine"):
        print(f"[INFO] pipeline detection_engine={pipe.get('detection_engine')}")

    twin = get_json("/api/v1/twin/snapshot")
    zones = twin.get("zones") or []
    assert len(zones) >= 4
    alerts = twin.get("alerts") or []
    print(f"[PASS] twin zones={len(zones)} alerts={len(alerts)}")

    # Ensure we have an actionable alert (reset if pipeline left only green)
    if not alerts:
        hot = post("/api/v1/twin/reset-metrics")
        alerts = hot.get("alerts") or []
    assert alerts, "need at least one alert for decision queue"
    alert = alerts[0]
    actions = alert.get("actions") or []
    assert actions, "expected GB recommendations"
    conf = actions[0].get("confidence")
    print(
        f"[PASS] explainable alert zone={alert.get('zone_code')} "
        f"actions={len(actions)} conf0={conf}"
    )

    ack = post_json(
        "/api/v1/decisions/ack",
        {
            "alert_id": alert["id"],
            "action_type": actions[0]["action_type"],
            "status": "accepted",
        },
    )
    assert ack.get("ok") is True
    print(f"[PASS] accepted action {actions[0]['action_type']}")

    sim = post_json(
        "/api/v1/simulation/what-if",
        {
            "name": "day23-close-gate-c",
            "close_exits": ["Gate-C"],
            "rainfall_mm_h": 0,
            "vip_zone": None,
            "hold_ingress": False,
            "horizon_minutes": 10,
        },
    )
    assert "predicted_peak_dcrs" in sim
    print(
        f"[PASS] what-if close Gate-C "
        f"peak={sim.get('predicted_peak_dcrs')} delta={sim.get('dcrs_delta')}"
    )

    report = post_json(
        "/api/v1/reports/incident",
        {"use_live_twin": True, "event_name": "Day23 Rehearsal"},
    )
    md = report.get("markdown") or ""
    assert len(md) > 100
    print(f"[PASS] incident report source={report.get('source')} chars={len(md)}")

    trends = get_json("/api/v1/analytics/trends")
    assert trends.get("points") or trends.get("zone_code")
    print(f"[PASS] trends source={trends.get('source')} zone={trends.get('zone_code')}")

    print("Day 23 verification OK — full API rehearsal passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
