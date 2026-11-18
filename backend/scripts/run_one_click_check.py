import json
import urllib.request

# 1. Login
data = json.dumps({"username": "tsp.operator", "password": "Operator@TS2026"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/auth/login",
    data=data,
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["access_token"]
print("Logged in successfully. Token received.\n")

# 2. Get initial twin snapshot
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/twin/snapshot",
    headers={"Authorization": f"Bearer {token}"},
)
snap = json.loads(urllib.request.urlopen(req).read())
print("=== INITIAL TWIN SNAPSHOT (BEFORE RUN) ===")
for card in snap.get("zones", []):
    z = card.get("zone", {})
    code = z.get("code")
    status = card.get("status")
    metrics = card.get("metrics") or {}
    risk = card.get("risk") or {}
    print(f"Zone {code}: status={status}, count={metrics.get('count')}, dcrs={risk.get('dcrs')}, band={risk.get('band')}")

# 3. Run One-Click Full Pipeline on mall_dataset.mp4
print("\n=== RUNNING ONE-CLICK FULL PIPELINE (POST /api/v1/pipeline/run) ===")
pipe_data = json.dumps({
    "sample_filename": "mall_dataset.mp4",
    "frame_stride": 4,
    "max_frames": 60,
    "include_twin": True,
}).encode()
pipe_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/pipeline/run",
    data=pipe_data,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
)
pipe_resp = urllib.request.urlopen(pipe_req)
pipe_result = json.loads(pipe_resp.read())
print(f"Pipeline finished! Elapsed: {pipe_result.get('elapsed_ms')} ms")
print(f"Peak zone: {pipe_result.get('peak_zone')}, Peak DCRS: {pipe_result.get('peak_dcrs')}")

# 4. Get twin snapshot after run
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/twin/snapshot",
    headers={"Authorization": f"Bearer {token}"},
)
after_snap = json.loads(urllib.request.urlopen(req).read())
print("\n=== TWIN SNAPSHOT AFTER PIPELINE RUN ===")
for card in after_snap.get("zones", []):
    z = card.get("zone", {})
    code = z.get("code")
    status = card.get("status")
    metrics = card.get("metrics") or {}
    risk = card.get("risk") or {}
    print(f"Zone {code}: status={status}, count={metrics.get('count')}, dcrs={risk.get('dcrs')}, band={risk.get('band')}")
