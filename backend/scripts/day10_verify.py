"""Day 10 verify — explainable alert narratives (ERA)."""

from __future__ import annotations

import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path: str):
    with urllib.request.urlopen(BASE + path, timeout=60) as resp:
        return json.loads(resp.read().decode())


def post(path: str, data: bytes = b""):
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    health = get("/health")
    assert health.get("status") == "ok"

    result = post("/api/v1/twin/reset-metrics")
    assert result.get("peak_band") in ("orange", "red"), result.get("peak_band")
    assert result.get("alerts"), "expected Orange/Red alerts with explanations"

    alert = result["alerts"][0]
    expl = alert.get("explanation")
    assert isinstance(expl, dict), expl
    assert "narrative" in expl and "Reason:" in expl["narrative"]
    assert expl.get("contributions") and len(expl["contributions"]) >= 1
    labels = " ".join(c.get("label", "") for c in expl["contributions"])
    assert any(
        key in labels or key in expl["narrative"]
        for key in (
            "density",
            "Exit queue",
            "Walking speed",
            "Opposing",
            "Crowd density",
            "Predicted surge",
        )
    ), (labels, expl["narrative"])
    print(
        "[PASS] alert why",
        f"zone={alert['zone_code']} band={alert['band']} top={expl.get('top_labels')}",
    )

    zone = next(z for z in result["zones"] if z["zone"]["code"] == result["peak_zone"])
    zexpl = zone.get("explanation") or {}
    assert zexpl.get("narrative") and zexpl.get("contributions")
    print(
        "[PASS] zone ERA",
        f"dcrs={zone['risk']['dcrs']} factors={len(zexpl['contributions'])}",
    )

    alerts = get("/api/v1/risk/alerts?limit=5")
    assert alerts and isinstance(alerts[0].get("explanation"), dict)
    print("[PASS] GET /risk/alerts carries ERA payload")

    twin = get("/api/v1/twin/snapshot")
    assert twin.get("alerts")
    print("[PASS] twin snapshot alerts", len(twin["alerts"]))
    print("Day 10 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
