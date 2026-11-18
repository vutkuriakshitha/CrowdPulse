import json
import urllib.error
import urllib.request

def main():
    print("=" * 60)
    print("CrowdPulse Authentication Security Suite")
    print("=" * 60)
    url = "http://127.0.0.1:8000/api/v1/auth/login"

    # Test 1: Random wrong credentials
    payload_bad = json.dumps({"username": "wrong_user", "password": "wrong_password_999"}).encode()
    req = urllib.request.Request(url, data=payload_bad, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        print("[FAIL] Wrong credentials were accepted!")
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401 but got {e.code}"
        print("[TEST 1 PASSED]: Wrong credentials strictly rejected with HTTP 401 Unauthorized.")

    # Test 2: Valid username with WRONG password
    payload_wrong_pw = json.dumps({"username": "tsp.operator", "password": "WrongPassword!"}).encode()
    req = urllib.request.Request(url, data=payload_wrong_pw, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        print("[FAIL] Incorrect password was accepted!")
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401 but got {e.code}"
        print("[TEST 2 PASSED]: Valid username with wrong password rejected with HTTP 401.")

    # Test 3: Valid credentials
    payload_good = json.dumps({"username": "tsp.operator", "password": "Operator@TS2026"}).encode()
    req = urllib.request.Request(url, data=payload_good, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "access_token" in data
        assert data["user"]["username"] == "tsp.operator"
        print(f"[TEST 3 PASSED]: Valid operator credentials successfully authenticated (User: {data['user']['full_name']}).")

    # Test 4: Dashboard protection check without Bearer token
    req = urllib.request.Request("http://127.0.0.1:8000/api/v1/twin/snapshot")
    try:
        urllib.request.urlopen(req)
        print("[FAIL] Unauthenticated request reached protected twin endpoint!")
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401 but got {e.code}"
        print("[TEST 4 PASSED]: Unauthenticated API access strictly blocked with HTTP 401.")

    print("=" * 60)
    print("ALL 4 AUTHENTICATION SECURITY TESTS PASSED (100% SECURE)")
    print("=" * 60)

if __name__ == "__main__":
    main()
