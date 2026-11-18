import sys
import urllib.parse
import urllib.request

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from cp_http import BASE, ensure_login  # noqa: E402

tok = ensure_login()
vid = "66d30998-e765-4846-89fa-28f479c4f9d5"
q = urllib.parse.urlencode({"token": tok})
for kind in ("annotated", "preview"):
    url = f"{BASE}/api/v1/videos/{vid}/{kind}?{q}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read(16)
            print(kind.upper(), "OK", r.status, r.headers.get("content-type"), list(data[:8]))
    except Exception as e:
        print(kind.upper(), "FAIL", e)
