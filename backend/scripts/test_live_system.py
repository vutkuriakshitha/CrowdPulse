import urllib.request
import json

def main():
    print("=" * 60)
    print("CrowdPulse Live Full-Stack Verification")
    print("=" * 60)

    # 1. Backend Health
    with urllib.request.urlopen("http://localhost:8000/health") as resp:
        h = json.loads(resp.read().decode())
        print(f"[1/5] Backend Health: {h['status']} (Service: {h['service']} v{h['version']})")

    # 2. Operator Authentication
    payload = json.dumps({"username": "tsp.operator", "password": "Operator@TS2026"}).encode()
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        auth_data = json.loads(resp.read().decode())
        token = auth_data["access_token"]
        user = auth_data["user"]
        print(f"[2/5] Operator Auth: OK ({user['full_name']} | Role: {user['role']} | Unit: {user['unit']})")

    # 3. Digital Twin Snapshot
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/twin/snapshot",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as resp:
        twin = json.loads(resp.read().decode())
        zones = twin.get("zones", [])
        alerts = twin.get("alerts", [])
        print(f"[3/5] Digital Twin: OK ({len(zones)} concourse zones monitored, {len(alerts)} active alerts)")

    # 4. Frontend /login route
    with urllib.request.urlopen("http://localhost:3000/login") as resp:
        print(f"[4/5] Frontend /login: HTTP {resp.status} OK (Ready for operator login)")

    # 5. Frontend / root console route
    with urllib.request.urlopen("http://localhost:3000/") as resp:
        print(f"[5/5] Frontend / (Dashboard): HTTP {resp.status} OK (Operations console alive)")

    print("=" * 60)
    print("ALL 5 SYSTEM CHECKS PASSED: READY FOR USER INTERACTION")
    print("=" * 60)

if __name__ == "__main__":
    main()
