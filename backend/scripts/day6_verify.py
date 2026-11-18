"""Day 6 verify — person detection timeline on CCTV video."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"


def upload(path: Path) -> dict:
    boundary = "----CPBoundaryDay6"
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
    # ensure synthetic sample exists
    from make_synthetic_crowd_video import main as make_video

    video_path = make_video()

    with urllib.request.urlopen(BASE + "/api/v1/videos/detector/status", timeout=60) as resp:
        status = json.loads(resp.read().decode())
    print("[PASS] detector", status)

    uploaded = upload(video_path)
    print("[PASS] upload", uploaded["id"])

    req = urllib.request.Request(
        BASE + f"/api/v1/videos/{uploaded['id']}/process?frame_stride=5&max_frames=40",
        method="POST",
        data=b"",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode())

    assert "timeline" in result and len(result["timeline"]) > 0
    assert "summary" in result
    print(
        "[PASS] process",
        f"engine={result['engine']}",
        f"backend={result['backend']}",
        f"points={len(result['timeline'])}",
        f"max={result['summary']['max_count']}",
        f"avg={result['summary']['avg_count']}",
    )

    with urllib.request.urlopen(BASE + f"/api/v1/videos/{uploaded['id']}/detections", timeout=60) as resp:
        det = json.loads(resp.read().decode())
    assert len(det["timeline"]) > 0
    print("[PASS] detections persisted", det["run_id"])
    print("Day 6 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
