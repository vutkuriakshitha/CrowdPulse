"""Day 18 verify — hotspot ranking + trends payload for dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, get_json, post, public_get  # noqa: E402

ensure_login()


def main() -> int:
    _, health = public_get("/health")
    assert health.get("status") == "ok"
    post("/api/v1/twin/reset-metrics")

    hot = get_json("/api/v1/analytics/hotspots")
    rows = hot.get("hotspots") or []
    assert len(rows) >= 4, rows
    assert rows[0]["rank"] == 1
    assert "rank_score" in rows[0] and "current_dcrs" in rows[0] and "band" in rows[0]
    scores = [r["rank_score"] for r in rows]
    assert scores == sorted(scores, reverse=True), scores
    print(
        f"[PASS] hotspots ranked {[r['zone_code'] for r in rows]} "
        f"top={rows[0]['zone_code']} dcrs={rows[0]['current_dcrs']}"
    )

    trends = get_json("/api/v1/analytics/trends")
    assert trends.get("zone_code")
    assert trends.get("source") in ("detection_run", "risk_snapshots", "synthetic_twin")
    points = trends.get("points") or []
    assert len(points) >= 2, points
    assert "density" in points[0] and "dcrs" in points[0]
    print(f"[PASS] trends source={trends['source']} zone={trends['zone_code']} n={len(points)}")

    # Optional zone filter
    trends_b = get_json("/api/v1/analytics/trends?zone=B")
    assert trends_b.get("zone_code") == "B"
    print("[PASS] trends zone filter B")

    print("Day 18 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
