"""Day 8 verify — zone analytics metrics from tracks."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"


def upload(path: Path) -> dict:
    boundary = "----CPBoundaryDay8"
    data = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + "/api/v1/videos/upload",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    from make_synthetic_crowd_video import main as make_video

    video_path = make_video()
    uploaded = upload(video_path)
    print("[PASS] upload", uploaded["id"])

    req = urllib.request.Request(
        BASE + f"/api/v1/videos/{uploaded['id']}/process?frame_stride=5&max_frames=40",
        method="POST",
        data=b"",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode())

    zs = result["zone_summary"]
    assert len(zs) >= 4
    required = ["density", "mean_speed", "opposing_flow", "congestion_index", "exit_pressure"]
    for code, row in zs.items():
        for key in required:
            assert key in row, f"missing {key} in zone {code}"
    print(
        "[PASS] zone analytics",
        {
            k: {
                "count": v["latest_count"],
                "dens": v["density"],
                "spd": v["mean_speed"],
                "opp": v["opposing_flow"],
                "cong": v["congestion_index"],
            }
            for k, v in zs.items()
        },
    )

    with urllib.request.urlopen(BASE + "/api/v1/twin/snapshot", timeout=120) as resp:
        twin = json.loads(resp.read().decode())
    sample = twin["zones"][0]["metrics"]
    for key in ["density", "mean_speed", "opposing_flow", "exit_pressure", "abnormal_motion"]:
        assert key in sample
    print(
        "[PASS] twin metrics",
        {
            z["zone"]["code"]: {
                "count": z["metrics"]["count"],
                "spd": z["metrics"]["mean_speed"],
                "opp": z["metrics"]["opposing_flow"],
            }
            for z in twin["zones"]
        },
    )
    print("Day 8 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
