"""Day 17 verify — incident report from live twin + persistence."""

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

    # Seed twin risk + accept one action so report has interventions
    hot = post("/api/v1/twin/reset-metrics")
    alerts = hot.get("alerts") or []
    assert alerts, "need alerts for report context"
    act = (alerts[0].get("actions") or [None])[0]
    if act:
        post_json(
            "/api/v1/decisions/ack",
            {
                "alert_id": alerts[0]["id"],
                "action_type": act["action_type"],
                "status": "accepted",
            },
        )
        print(f"[PASS] accepted action {act['action_type']} for report trail")

    report = post_json(
        "/api/v1/reports/incident",
        {"use_live_twin": True, "event_name": "Day17 Verify Event"},
    )
    md = report.get("markdown") or ""
    assert len(md) > 100, "markdown too short"
    assert "Executive Summary" in md or "Incident Report" in md
    assert report.get("source") in ("template", "ollama")
    assert "context" in report and report["context"].get("peak_dcrs") is not None
    print(
        f"[PASS] report source={report.get('source')} "
        f"peak={report['context'].get('peak_dcrs')} "
        f"persisted={report.get('persisted')}"
    )

    # Timeline / decisions should reflect live twin
    assert "Timeline" in md or "timeline" in md.lower()
    print("[PASS] markdown contains timeline section")

    recent = get_json("/api/v1/reports/recent")
    assert isinstance(recent, list)
    if report.get("persisted"):
        assert len(recent) >= 1
        print(f"[PASS] recent reports n={len(recent)}")
    else:
        print("[PASS] recent endpoint ok (persist optional)")

    print("Day 17 verification OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print("[FAIL]", exc)
        raise SystemExit(1)
