"""Day 11 verify — Gradient Boosting recommendations on high-risk alerts."""

from __future__ import annotations

import json
import urllib.request

BASE = "http://127.0.0.1:8000"

CORE = {"open_exit", "deploy_guards", "activate_pa"}


def get(path: str):
    with urllib.request.urlopen(BASE + path, timeout=120) as resp:
        return json.loads(resp.read().decode())


def post(path: str, data: bytes = b""):
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    health = get("/health")
    assert health.get("status") == "ok"

    status = get("/api/v1/decisions/recommender/status")
    assert status.get("algorithm") == "GradientBoostingClassifier"
    assert status.get("fitted") is True
    assert "open_exit" in status.get("actions", [])
    print(
        "[PASS] recommender status",
        f"fitted={status['fitted']} disk={status.get('model_cached_on_disk')} actions={len(status.get('actions', []))}",
    )

    result = post("/api/v1/twin/reset-metrics")
    assert result.get("peak_band") in ("orange", "red")
    alerts = result.get("alerts") or []
    assert alerts, "expected high-risk alerts with GB actions"

    found_core = set()
    for alert in alerts:
        actions = alert.get("actions") or []
        assert actions, f"alert {alert.get('zone_code')} missing actions"
        assert "Gradient Boosting" in (alert.get("rationale") or "")
        confs = [a.get("confidence", 0) for a in actions]
        assert confs == sorted(confs, reverse=True), confs
        for a in actions:
            assert 0.0 <= float(a.get("confidence", -1)) <= 1.0
            found_core.add(a.get("action_type"))
        titles = " | ".join(a.get("title", "") for a in actions)
        print(
            f"[PASS] alert zone={alert['zone_code']} band={alert['band']} "
            f"n={len(actions)} types={[a.get('action_type') for a in actions[:4]]}"
        )
        assert any(
            key in titles.lower()
            for key in ("open exit", "deploy", "announcement", "public announcement", "guards")
        ), titles

    assert found_core & CORE, found_core
    print("[PASS] core actions present", sorted(found_core & CORE))

    decisions = get("/api/v1/decisions?limit=10")
    assert decisions and decisions[0].get("actions")
    print("[PASS] GET /decisions", len(decisions), "bundles")
    print("Day 11 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
