import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cp_http import ensure_login, get_json  # noqa: E402

ensure_login()
print("ann files", [p.name for p in Path("data/uploads/annotated").glob("*_annotated.mp4")])
vids = get_json("/api/v1/videos/")
for v in vids[:8]:
    try:
        d = get_json(f"/api/v1/videos/{v['id']}/detections")
        print(
            v["original_filename"],
            v["id"][:8],
            "ann=",
            d.get("annotated_url"),
            "max=",
            (d.get("summary") or {}).get("max_count"),
        )
    except Exception as e:
        print(v["original_filename"], "no det", e)
