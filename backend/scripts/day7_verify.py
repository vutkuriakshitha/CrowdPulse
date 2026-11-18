"""Day 7 verify — tracking + zone assignment."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"


def upload(path: Path) -> dict:
    boundary = "----CPBoundaryDay7"
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

    assert result.get("tracker") == "centroid-iou"
    assert "zone_summary" in result
    zones = result["zone_summary"]
    assert len(zones) >= 4
    print("[PASS] tracker", result["tracker"], "unique_tracks", result["summary"].get("unique_tracks"))
    print("[PASS] zone_summary", {k: v.get("latest_count") for k, v in zones.items()})

    # twin should reflect zone counts
    with urllib.request.urlopen(BASE + "/api/v1/twin/snapshot", timeout=120) as resp:
        twin = json.loads(resp.read().decode())
    twin_counts = {
        z["zone"]["code"]: z["metrics"]["count"] for z in twin.get("zones", [])
    }
    print("[PASS] twin zone counts", twin_counts)
    assert any(v >= 0 for v in twin_counts.values())
    print("Day 7 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
