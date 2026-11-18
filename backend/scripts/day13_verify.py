"""Day 13 verify — twin zones carry DCRS band for live map coloring."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, get_json, post, post_json, public_get  # noqa: E402

ensure_login()


def assert_map_payload(snap: dict, *, require_hot: bool = False) -> None:
    zones = snap.get("zones") or []
    assert len(zones) >= 4, zones
    for z in zones:
        assert "risk" in z and "band" in z["risk"] and "dcrs" in z["risk"]
        assert z["risk"]["band"] in ("green", "yellow", "orange", "red")
        assert "metrics" in z and "density" in z["metrics"]
        assert "zone" in z and "code" in z["zone"] and "polygon" in z["zone"]
    bands = {z["zone"]["code"]: z["risk"]["band"] for z in zones}
    dcrs = {z["zone"]["code"]: z["risk"]["dcrs"] for z in zones}
    if require_hot:
        assert any(b in ("orange", "red") for b in bands.values()), bands
    print("[PASS] twin map payload", bands, {k: round(v, 1) for k, v in dcrs.items()})


def main() -> int:
    _, health = public_get("/health")
    assert health.get("status") == "ok"

    # Seeded dense Zone B → map should show O/R
    hot = post("/api/v1/twin/reset-metrics")
    assert_map_payload(hot, require_hot=True)
    assert hot.get("peak_zone") == "B"
    assert hot.get("peak_band") in ("orange", "red")
    print(f"[PASS] seeded peak {hot['peak_zone']}:{hot['peak_band']} dcrs={hot['peak_dcrs']}")

    # Pipeline updates twin (map refresh source)
    pipe = post_json(
        "/api/v1/pipeline/run",
        {"sample_filename": "synthetic_crowd.mp4", "frame_stride": 5, "max_frames": 30, "include_twin": True},
    )
    assert pipe.get("ok") and pipe.get("twin")
    assert_map_payload(pipe["twin"], require_hot=False)
    print(
        "[PASS] pipeline twin for map",
        f"peak={pipe.get('peak_zone')}:{pipe.get('peak_band')}",
    )

    snap = get_json("/api/v1/twin/snapshot")
    assert_map_payload(snap, require_hot=False)
    print("Day 13 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
