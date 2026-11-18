"""Day 19 verify — bad video / empty file handling + healthy pipeline still works."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import BASE, ensure_login, get_json, post_json, public_get, _headers  # noqa: E402

ensure_login()


def upload_bytes(filename: str, data: bytes, content_type: str = "video/mp4") -> tuple[int, dict | str]:
    boundary = "----cpday19"
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {content_type}\r\n\r\n".encode()
    body += data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + "/api/v1/videos/upload",
        data=body,
        method="POST",
        headers={
            **_headers(),
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def process(video_id: str) -> tuple[int, dict | str]:
    req = urllib.request.Request(
        BASE + f"/api/v1/videos/{video_id}/process?frame_stride=10&max_frames=10",
        data=b"",
        method="POST",
        headers=_headers(),
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def main() -> int:
    _, health = public_get("/health")
    assert health.get("status") == "ok"

    # Tiny/empty-ish payload should fail validation (400) either on upload or process
    code, bad = upload_bytes("corrupt_day19.bin", b"NOT_A_VIDEO" + b"\x00" * 8, "application/octet-stream")
    # upload may accept odd content-type with warning, or reject — both ok if process fails cleanly
    if code == 200 and isinstance(bad, dict) and bad.get("id"):
        pcode, perr = process(bad["id"])
        assert pcode in (400, 500), (pcode, perr)
        detail = perr.get("detail") if isinstance(perr, dict) else str(perr)
        assert detail, perr
        print(f"[PASS] corrupt video process rejected status={pcode} detail={str(detail)[:80]}")
    else:
        assert code in (400, 415, 422), (code, bad)
        print(f"[PASS] corrupt upload rejected status={code}")

    # Healthy pipeline still works
    pipe = post_json(
        "/api/v1/pipeline/run",
        {
            "sample_filename": "synthetic_crowd.mp4",
            "frame_stride": 5,
            "max_frames": 20,
            "include_twin": True,
        },
    )
    assert pipe.get("ok") is True
    assert pipe.get("stages")
    print(
        f"[PASS] healthy pipeline ok stages={[s.get('name') for s in pipe.get('stages') or []]} "
        f"empty={pipe.get('empty_detections')}"
    )

    # API failures should be JSON, not crash
    code404, _ = process("00000000-0000-0000-0000-000000000099")
    assert code404 == 404
    print("[PASS] missing video_id returns 404")

    twin = get_json("/api/v1/twin/snapshot")
    assert "zones" in twin
    print("Day 19 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
