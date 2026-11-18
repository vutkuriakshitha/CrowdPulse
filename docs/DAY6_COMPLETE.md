# Day 6 Completion Log — CrowdPulse Level A

**Date:** 2026-07-15  
**Status:** COMPLETE

## Done today
1. Person detection engine abstraction
   - Primary: **Ultralytics YOLO** (when installed)
   - Fallback: **OpenCV HOG** pedestrian detector (CPU, reliable)
2. Video processor → frame stride sampling → **count timeline**
3. `detection_runs` table persists engine/summary/timeline
4. APIs:
   - `GET /api/v1/videos/detector/status`
   - `POST /api/v1/videos/{id}/process`
   - `GET /api/v1/videos/{id}/detections`
5. Dashboard **Process Video** runs detection and shows timeline
6. Synthetic sample clip generator for pipeline testing

## Verified
```
[PASS] detector {'engine': 'hog-pedestrian', 'backend': 'opencv'}
[PASS] upload
[PASS] process ... points=12 max=2 avg=0.667
[PASS] detections persisted
Day 6 verification OK
```

## How to use
1. Upload a real CCTV mp4 in the dashboard
2. Click **Process Video**
3. See count timeline (persons per sampled frame)

## Enable YOLO (recommended when laptop allows)
```bash
cd backend
.\.venv\Scripts\Activate.ps1
pip install ultralytics
# restart API
```
Then detector status becomes `ultralytics-yolo / yolov8n.pt`.

## Next — Day 7
Tracking + zone assignment from detections.
