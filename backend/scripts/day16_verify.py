"""Day 16 verify — what-if response shape required by the polished UI."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, post, post_json, public_get  # noqa: E402

ensure_login()

REQUIRED = (
    "narrative",
    "predicted_peak_dcrs",
    "baseline_peak_dcrs",
    "dcrs_delta",
    "congested_zones",
    "zone_risks",
    "recommended_actions",
)


def main() -> int:
    _, health = public_get("/health")
    assert health.get("status") == "ok"
    post("/api/v1/twin/reset-metrics")

    data = post_json(
        "/api/v1/simulation/what-if",
        {
            "name": "Close Gate-C",
            "close_exits": ["Gate-C"],
            "rainfall_mm_h": 0,
            "vip_zone": None,
            "hold_ingress": False,
            "horizon_minutes": 10,
        },
    )
    for key in REQUIRED:
        assert key in data, f"missing UI field: {key}"

    assert isinstance(data["narrative"], str) and len(data["narrative"]) > 20
    assert isinstance(data["zone_risks"], list) and len(data["zone_risks"]) >= 4
    assert data["dcrs_delta"] > 0, data["dcrs_delta"]
    assert isinstance(data["recommended_actions"], list)

    for z in data["zone_risks"]:
        assert "zone_code" in z and "dcrs" in z and "band" in z

    print("[PASS] UI payload fields present")
    print(
        f"[PASS] narrative + peak={data['predicted_peak_dcrs']} "
        f"delta={data['dcrs_delta']} actions={len(data['recommended_actions'])}"
    )
    print("Day 16 verification OK — run Demo: Close Gate-C on the dashboard")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
