# Day 21 Completion Log — CrowdPulse Level A

**Date:** 2026-07-16  
**Status:** COMPLETE

## Done today
1. **Demo sampling defaults** — `DEMO_FRAME_STRIDE=8`, `DEMO_MAX_FRAMES=24`
2. **YOLO nano + small imgsz** — `yolov8n.pt`, `imgsz=320` (HOG also downscales + faster stride)
3. **In-memory caches** — detector + GB recommender `@lru_cache`; warmed on API startup
4. **UI** — one-click / samples use stride 8 / max 24
5. Verify: `backend/scripts/day21_verify.py` (dense pack &lt; 2 min)

## Target
Short clip processes in **&lt; 1–2 minutes** for viva.

## Next — Day 22
Panel docs (synopsis, architecture, tech list, dataset).
