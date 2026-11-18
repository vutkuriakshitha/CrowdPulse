"""Day 2 smoke test — verifies CrowdPulse API skeleton routes + auth."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login  # noqa: E402

BASE = "http://127.0.0.1:8000"
_TOKEN: str | None = None


def call(method: str, path: str, body: dict | None = None, *, auth: bool = True) -> tuple[int, dict | list | str]:
    data = None if body is None else json.dumps(body).encode()
    headers: dict[str, str] = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if auth and _TOKEN:
        headers["Authorization"] = f"Bearer {_TOKEN}"
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="ignore")
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def main() -> int:
    global _TOKEN
    checks = []

    def add(name: str, ok: bool, detail: str = ""):
        checks.append((name, ok, detail))
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name} {detail}")

    code, health = call("GET", "/health", auth=False)
    add("GET /health", code == 200 and isinstance(health, dict) and health.get("service") == "crowdpulse", str(health))

    code, docs = call("GET", "/docs", auth=False)
    add("GET /docs", code == 200, f"status={code}")

    code, openapi = call("GET", "/openapi.json", auth=False)
    add("GET /openapi.json", code == 200 and isinstance(openapi, dict) and "paths" in openapi, f"paths={len(openapi.get('paths', {})) if isinstance(openapi, dict) else 0}")

    code, login = call(
        "POST",
        "/api/v1/auth/login",
        {"username": "tsp.operator", "password": "Operator@TS2026"},
        auth=False,
    )
    add("POST /api/v1/auth/login", code == 200 and isinstance(login, dict) and "access_token" in login, f"status={code}")
    if isinstance(login, dict) and login.get("access_token"):
        _TOKEN = login["access_token"]
    else:
        _TOKEN = ensure_login()

    code, me = call("GET", "/api/v1/auth/me")
    add("GET /api/v1/auth/me", code == 200 and isinstance(me, dict) and me.get("role") in ("operator", "admin"), str(me)[:120])

    code, denied = call("GET", "/api/v1/twin/snapshot", auth=False)
    add("unauthenticated twin blocked", code == 401, f"status={code}")

    code, root = call("GET", "/api/v1")
    add("GET /api/v1", code == 200 and isinstance(root, dict) and "modules" in root, str(root)[:120])

    code, venues = call("GET", "/api/v1/venues")
    add("GET /api/v1/venues", code == 200, f"status={code}")

    code, twin = call("GET", "/api/v1/twin/snapshot")
    add("GET /api/v1/twin/snapshot", code == 200 and isinstance(twin, dict) and "zones" in twin, f"zones={len(twin.get('zones', [])) if isinstance(twin, dict) else 0}")

    code, risk = call("POST", "/api/v1/risk/evaluate")
    add("POST /api/v1/risk/evaluate", code == 200, f"status={code}")

    code, alerts = call("GET", "/api/v1/risk/alerts")
    add("GET /api/v1/risk/alerts", code == 200, f"status={code}")

    code, decisions = call("GET", "/api/v1/decisions")
    add("GET /api/v1/decisions", code == 200, f"status={code}")

    code, sim = call(
        "POST",
        "/api/v1/simulation/what-if",
        {
            "name": "day2-check",
            "close_exits": ["Gate-C"],
            "rainfall_mm_h": 5,
            "vip_zone": "B",
            "horizon_minutes": 10,
        },
    )
    add("POST /api/v1/simulation/what-if", code == 200 and isinstance(sim, dict), f"status={code}")

    code, hotspots = call("GET", "/api/v1/analytics/hotspots")
    add("GET /api/v1/analytics/hotspots", code == 200, f"status={code}")

    code, trends = call("GET", "/api/v1/analytics/trends")
    add("GET /api/v1/analytics/trends", code == 200, f"status={code}")

    code, report = call("POST", "/api/v1/reports/incident", {})
    add("POST /api/v1/reports/incident", code == 200 and isinstance(report, dict) and "markdown" in report, f"status={code}")

    failed = [c for c in checks if not c[1]]
    print("-" * 60)
    print(f"Passed {len(checks) - len(failed)}/{len(checks)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
