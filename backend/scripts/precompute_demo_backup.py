"""Day 20 — precompute dense-clip pipeline result for backup demo (JSON)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, post_json, public_get  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data" / "demo_backup" / "dense_pipeline_result.json"


def main() -> int:
    ensure_login()
    _, health = public_get("/health")
    assert health.get("status") == "ok"

    # Prefer dense sample; pipeline registers it if present
    result = post_json(
        "/api/v1/pipeline/run",
        {
            "sample_filename": "dense_crowd.mp4",
            "frame_stride": 5,
            "max_frames": 40,
            "include_twin": True,
        },
    )
    assert result.get("ok") is True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Store a compact backup (drop huge twin if needed — keep essentials)
    backup = {
        "ok": result.get("ok"),
        "pipeline": result.get("pipeline"),
        "elapsed_ms": result.get("elapsed_ms"),
        "stages": result.get("stages"),
        "peak_dcrs": result.get("peak_dcrs"),
        "peak_zone": result.get("peak_zone"),
        "peak_band": result.get("peak_band"),
        "engine": result.get("engine"),
        "backend": result.get("backend"),
        "tracker": result.get("tracker"),
        "summary": result.get("summary"),
        "zone_summary": result.get("zone_summary"),
        "risk_by_zone": result.get("risk_by_zone"),
        "alerts": [
            {
                "id": a.get("id"),
                "zone_code": a.get("zone_code"),
                "dcrs": a.get("dcrs"),
                "band": a.get("band"),
                "actions": [
                    {
                        "action_type": x.get("action_type"),
                        "title": x.get("title"),
                        "confidence": x.get("confidence"),
                    }
                    for x in (a.get("actions") or [])[:5]
                ],
            }
            for a in (result.get("alerts") or [])[:8]
        ],
        "timeline_head": (result.get("timeline") or [])[:15],
        "sample_filename": "dense_crowd.mp4",
        "note": "Backup demo snapshot — use if live processing is too slow for viva.",
    }
    OUT.write_text(json.dumps(backup, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print(
        f"peak={backup['peak_zone']}:{backup['peak_band']} "
        f"DCRS={backup['peak_dcrs']} elapsed_ms={backup['elapsed_ms']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
