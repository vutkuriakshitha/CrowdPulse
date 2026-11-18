"""Day 12 verify — one-click POST /api/v1/pipeline/run."""

from __future__ import annotations

import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path: str):
    with urllib.request.urlopen(BASE + path, timeout=60) as resp:
        return json.loads(resp.read().decode())


def post_json(path: str, payload: dict):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    health = get("/health")
    assert health.get("status") == "ok"

    status = get("/api/v1/pipeline/status")
    assert "detect" in status.get("flow", [])
    print("[PASS] pipeline status", " -> ".join(status["flow"]))

    result = post_json(
        "/api/v1/pipeline/run",
        {
            "sample_filename": "synthetic_crowd.mp4",
            "frame_stride": 5,
            "max_frames": 40,
            "include_twin": True,
        },
    )
    assert result.get("ok") is True
    assert result.get("risk_by_zone"), "missing risk_by_zone"
    assert result.get("zone_summary"), "missing zone_summary"
    assert result.get("peak_band") in ("green", "yellow", "orange", "red")
    stage_names = [s["name"] for s in result.get("stages", [])]
    for needed in ("resolve_video", "detect_track_analytics", "dcrs_era_recommend", "twin_snapshot"):
        assert needed in stage_names, stage_names
    assert result.get("twin") and result["twin"].get("zones")
    print(
        "[PASS] pipeline/run",
        f"elapsed={result.get('elapsed_ms')}ms peak={result.get('peak_zone')}:{result.get('peak_band')} "
        f"dcrs={result.get('peak_dcrs')} stages={stage_names}",
    )

    twin = get("/api/v1/twin/snapshot")
    assert twin.get("zones")
    print("[PASS] twin updated after pipeline", len(twin["zones"]), "zones")
    print("Day 12 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
