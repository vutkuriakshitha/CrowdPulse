"""Day 3 verification — DB-backed venues/zones/cameras."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cp_http import ensure_login, get, public_get  # noqa: E402

ensure_login()


def main() -> int:
    failures = 0

    def check(name: str, ok: bool, detail=""):
        nonlocal failures
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
        if not ok:
            failures += 1

    code, health = public_get("/health")
    check("health", code == 200 and health.get("database", {}).get("ok") is True, str(health))
    check("health venues>0", health.get("database", {}).get("venues", 0) >= 1)

    code, venues = get("/api/v1/venues/")
    check("list venues", code == 200 and isinstance(venues, list) and len(venues) >= 1, f"n={len(venues) if isinstance(venues, list) else 0}")

    code, demo = get("/api/v1/venues/demo")
    check("demo venue", code == 200 and demo.get("name") == "Aether Arena")
    zones = demo.get("zones", [])
    cams = demo.get("cameras", [])
    check("4 zones", len(zones) == 4, f"zones={len(zones)}")
    check("cameras>=3", len(cams) >= 3, f"cams={len(cams)}")
    check("zone fields", all("polygon" in z and "exits" in z and "capacity" in z for z in zones))

    venue_id = demo["id"]
    code, zlist = get(f"/api/v1/venues/{venue_id}/zones")
    check("zones by venue_id", code == 200 and len(zlist) == 4)

    code, clist = get(f"/api/v1/venues/{venue_id}/cameras")
    check("cameras by venue_id", code == 200 and len(clist) >= 3)

    code, twin = get("/api/v1/twin/snapshot")
    check("twin synced", code == 200 and len(twin.get("zones", [])) == 4)

    print("-" * 50)
    print(f"Passed checks with failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
