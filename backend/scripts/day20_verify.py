"""Day 20 verify — sample pack files exist and dense pipeline runs."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from make_sample_pack import PACK, OUT_DIR, main as make_pack  # noqa: E402
from cp_http import ensure_login, post_json, public_get  # noqa: E402

ensure_login()


def main() -> int:
    make_pack()
    for name, *_rest in PACK:
        path = OUT_DIR / name
        assert path.exists() and path.stat().st_size > 1000, path
        print(f"[PASS] sample present {name} bytes={path.stat().st_size}")

    syn = OUT_DIR / "synthetic_crowd.mp4"
    assert syn.exists(), syn
    print(f"[PASS] synthetic_crowd.mp4 alias present")

    _, health = public_get("/health")
    assert health.get("status") == "ok"

    dense = post_json(
        "/api/v1/pipeline/run",
        {
            "sample_filename": "dense_crowd.mp4",
            "frame_stride": 5,
            "max_frames": 25,
            "include_twin": True,
        },
    )
    assert dense.get("ok") is True
    print(
        f"[PASS] dense pipeline peak={dense.get('peak_zone')}:{dense.get('peak_band')} "
        f"DCRS={dense.get('peak_dcrs')}"
    )

    docs = Path(__file__).resolve().parents[2] / "docs" / "SAMPLE_CCTV_PACK.md"
    assert docs.exists(), docs
    print("[PASS] SAMPLE_CCTV_PACK.md present")
    print("Day 20 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
