"""Day 15 verify — closing an exit increases predicted peak DCRS."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, post, post_json, public_get  # noqa: E402

ensure_login()


def main() -> int:
    _, health = public_get("/health")
    assert health.get("status") == "ok"

    # Seed a hot twin so baseline is meaningful
    post("/api/v1/twin/reset-metrics")

    baseline = post_json(
        "/api/v1/simulation/what-if",
        {
            "name": "day15-baseline",
            "close_exits": [],
            "rainfall_mm_h": 0,
            "vip_zone": None,
            "hold_ingress": False,
            "horizon_minutes": 10,
        },
    )
    assert "predicted_peak_dcrs" in baseline
    assert "baseline_peak_dcrs" in baseline
    assert "zone_risks" in baseline and len(baseline["zone_risks"]) >= 4
    print(
        f"[PASS] baseline sim peak={baseline['predicted_peak_dcrs']} "
        f"delta={baseline.get('dcrs_delta')}"
    )

    closed = post_json(
        "/api/v1/simulation/what-if",
        {
            "name": "day15-close-gate-c",
            "close_exits": ["Gate-C"],
            "rainfall_mm_h": 0,
            "vip_zone": None,
            "hold_ingress": False,
            "horizon_minutes": 10,
        },
    )
    assert closed["predicted_peak_dcrs"] > baseline["predicted_peak_dcrs"], (
        closed["predicted_peak_dcrs"],
        baseline["predicted_peak_dcrs"],
    )
    assert closed.get("dcrs_delta", 0) > 0 or (
        closed["predicted_peak_dcrs"] > closed.get("baseline_peak_dcrs", 0)
    )
    print(
        f"[PASS] close Gate-C raises peak "
        f"{baseline['predicted_peak_dcrs']} -> {closed['predicted_peak_dcrs']} "
        f"(delta {closed.get('dcrs_delta')})"
    )

    # Affected zones that list Gate-C should show elevated exit pressure / risk
    zone_risks = {z["zone_code"]: z for z in closed.get("zone_risks") or []}
    # Gate-C is on zones B and C in seed
    for code in ("B", "C"):
        if code in zone_risks:
            assert "Gate-C" not in (zone_risks[code].get("exits_effective") or []), zone_risks[code]
    print("[PASS] Gate-C removed from effective exits on affected zones")

    rain = post_json(
        "/api/v1/simulation/what-if",
        {
            "name": "day15-rain",
            "close_exits": [],
            "rainfall_mm_h": 25,
            "vip_zone": None,
            "horizon_minutes": 10,
        },
    )
    assert rain["predicted_peak_dcrs"] >= baseline["predicted_peak_dcrs"]
    print(f"[PASS] rainfall sim peak={rain['predicted_peak_dcrs']}")

    vip = post_json(
        "/api/v1/simulation/what-if",
        {
            "name": "day15-vip",
            "close_exits": [],
            "rainfall_mm_h": 0,
            "vip_zone": "B",
            "horizon_minutes": 10,
        },
    )
    assert vip["predicted_peak_dcrs"] >= baseline["predicted_peak_dcrs"]
    print(f"[PASS] VIP zone B sim peak={vip['predicted_peak_dcrs']}")

    assert closed.get("simulation_id") or closed.get("persisted") is not None
    print(f"[PASS] simulation_id={closed.get('simulation_id')} persisted={closed.get('persisted')}")
    print("Day 15 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
