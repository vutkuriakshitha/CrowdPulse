"""Day 5 verify — CCTV video upload pipeline."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"


def main() -> int:
    # create tiny fake mp4 payload
    sample = Path(__file__).resolve().parents[1] / "data" / "uploads" / "_day5_test.mp4"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 256)

    boundary = "----CrowdPulseBoundary7MA4YWxkTrZu0gW"
    file_bytes = sample.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="day5_test.mp4"\r\n'
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}\r\n".encode() + (
        f'Content-Disposition: form-data; name="notes"\r\n\r\n'
        f"day5 verification upload\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    req = urllib.request.Request(
        BASE + "/api/v1/videos/upload",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        uploaded = json.loads(resp.read().decode())
    print("[PASS] upload", uploaded["id"], uploaded["status"], uploaded["size_bytes"])

    with urllib.request.urlopen(BASE + "/api/v1/videos/", timeout=30) as resp:
        listed = json.loads(resp.read().decode())
    assert any(v["id"] == uploaded["id"] for v in listed)
    print("[PASS] list videos", len(listed))

    req2 = urllib.request.Request(
        BASE + f"/api/v1/videos/{uploaded['id']}/queue",
        method="POST",
        data=b"",
    )
    with urllib.request.urlopen(req2, timeout=30) as resp:
        queued = json.loads(resp.read().decode())
    assert queued["status"] == "queued"
    print("[PASS] queue", queued["status"])

    with urllib.request.urlopen(BASE + "/api/v1/videos/samples", timeout=30) as resp:
        samples = json.loads(resp.read().decode())
    print("[PASS] samples endpoint", samples.get("hint", "")[:40])
    print("Day 5 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
