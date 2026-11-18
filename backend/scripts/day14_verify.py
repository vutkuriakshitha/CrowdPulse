"""Day 14 verify — decision queue Accept / Dismiss (ack API)."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, get_json, post, post_json, public_get  # noqa: E402

ensure_login()


def main() -> int:
    _, health = public_get("/health")
    assert health.get("status") == "ok"

    hot = post("/api/v1/twin/reset-metrics")
    alerts = hot.get("alerts") or []
    assert alerts, "expected orange/red alerts after reset-metrics"
    alert = alerts[0]
    actions = alert.get("actions") or []
    assert actions, "expected GB actions on alert"
    action_type = actions[0]["action_type"]
    print(f"[PASS] queue seeded zone={alert.get('zone_code')} actions={len(actions)}")

    # Accept first action as operator-capable admin token (tsp.admin from cp_http)
    ack = post_json(
        "/api/v1/decisions/ack",
        {"alert_id": alert["id"], "action_type": action_type, "status": "accepted"},
    )
    assert ack.get("ok") is True
    assert ack.get("action", {}).get("status") == "accepted"
    assert ack.get("action", {}).get("acked_by")
    print(f"[PASS] accept {action_type} by {ack['action'].get('acked_by')}")

    # Status survives twin snapshot refresh
    snap = get_json("/api/v1/twin/snapshot")
    found = next((a for a in snap.get("alerts") or [] if a.get("id") == alert["id"]), None)
    assert found, "alert missing after snapshot"
    matched = next((a for a in found.get("actions") or [] if a.get("action_type") == action_type), None)
    assert matched and matched.get("status") == "accepted", matched
    print("[PASS] accepted status survives twin snapshot")

    # Dismiss a different pending action if present
    pending = next(
        (a for a in found.get("actions") or [] if (a.get("status") or "pending") == "pending"),
        None,
    )
    if pending:
        d = post_json(
            "/api/v1/decisions/ack",
            {
                "alert_id": alert["id"],
                "action_type": pending["action_type"],
                "status": "dismissed",
            },
        )
        assert d.get("ok") and d["action"]["status"] == "dismissed"
        print(f"[PASS] dismiss {pending['action_type']}")
    else:
        print("[PASS] dismiss skipped (no second pending action)")

    decisions = get_json("/api/v1/decisions")
    assert isinstance(decisions, list) and len(decisions) >= 1
    print(f"[PASS] decisions list n={len(decisions)}")
    print("Day 14 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
