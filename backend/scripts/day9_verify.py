"""Day 9 verify — DCRS from metrics + video pipeline risk snapshots."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path
from uuid import uuid4

BASE = "http://127.0.0.1:8000"


def get(path: str):
    with urllib.request.urlopen(BASE + path, timeout=120) as resp:
        return json.loads(resp.read().decode())


def post(path: str, data: bytes = b""):
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())


def upload(path: Path) -> dict:
    boundary = "----CPBoundaryDay9"
    raw = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode() + raw + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + "/api/v1/videos/upload",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def test_dense_clip_dcrs() -> None:
    """Dense-clip style metrics → DCRS Orange/Red (engine-level acceptance)."""
    from app.ai.risk.dcrs import DCRSEngine
    from app.application.use_cases.process_video import camera_fov_density
    from app.domain.entities.crowd import RiskBand, ZoneMetrics

    dens = camera_fov_density(18, 400.0)  # Zone-B scale FOV density
    assert dens >= 0.9, dens

    engine = DCRSEngine()
    m = ZoneMetrics(
        zone_id=uuid4(),
        timestamp=0,
        count=18,
        density=round(dens, 4),
        mean_speed=0.35,
        opposing_flow=0.65,
        group_cohesion=0.4,
        abnormal_motion=0.45,
        exit_pressure=1.1,
        weather_factor=0.1,
        time_prior=0.6,
        historical_hotspot=0.45,
        emergency_flag=0.0,
        forecast_surge=0.9,
    )
    risk, _, _ = engine.evaluate(m)
    assert risk.dcrs >= 60, risk
    assert risk.band in (RiskBand.ORANGE, RiskBand.RED), risk
    print(f"[PASS] dense-clip DCRS band={risk.band.value} dcrs={risk.dcrs} dens={dens:.3f}")


def main() -> int:
    health = get("/health")
    assert health.get("status") == "ok"

    # Restore seeded dense Zone B, then evaluate → Orange/Red
    evaluated = post("/api/v1/twin/reset-metrics")
    assert evaluated.get("peak_band") in ("orange", "red"), evaluated.get("peak_band")
    assert evaluated.get("peak_zone") == "B", evaluated.get("peak_zone")
    print(
        "[PASS] live evaluate",
        f"zone={evaluated['peak_zone']} band={evaluated['peak_band']} dcrs={evaluated['peak_dcrs']}",
    )

    test_dense_clip_dcrs()

    from make_synthetic_crowd_video import main as make_video

    video_path = make_video()
    uploaded = upload(video_path)
    print("[PASS] upload", uploaded["id"])

    result = post(f"/api/v1/videos/{uploaded['id']}/process?frame_stride=5&max_frames=40")
    assert "risk_by_zone" in result and result["risk_by_zone"], list(result.keys())
    assert result.get("peak_band") in ("green", "yellow", "orange", "red")
    print(
        "[PASS] video->DCRS",
        {
            "peak": f"{result.get('peak_zone')}:{result.get('peak_band')}",
            "dcrs": result.get("peak_dcrs"),
            "zones": {
                k: {"dcrs": v["dcrs"], "band": v["band"]} for k, v in result["risk_by_zone"].items()
            },
        },
    )

    snaps = get(f"/api/v1/risk/snapshots?video_id={uploaded['id']}&limit=20")
    assert len(snaps) >= 1, snaps
    assert all("dcrs" in s and "band" in s for s in snaps)
    print("[PASS] risk snapshots", len(snaps), "rows")

    twin = get("/api/v1/twin/snapshot")
    bands = {z["zone"]["code"]: (z["risk"]["band"], z["risk"]["dcrs"]) for z in twin["zones"]}
    print("[PASS] twin after video", bands)
    print("Day 9 verification OK")
    return 0


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
