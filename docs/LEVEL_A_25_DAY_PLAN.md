# CrowdPulse — Level A End-to-End Daily Plan (25 Days)

**Goal:** Fully working major-project demo  
**Flow:** CCTV video → YOLO detection → zone analytics → DCRS risk → explanation → Gradient Boosting recommendations → dashboard → what-if → incident report  

**Definition of Done (Level A):**
- Upload/play one CCTV video (or webcam)
- System auto-runs full pipeline
- Dashboard shows zone colors, risk, reasons, actions
- What-if + incident report works
- You can demo confidently to panel in <10 minutes

---

## Week 1 — Foundation + Detection Pipeline

### Day 1 — Project freeze & CrowdPulse branding
**Do**
- Rename product branding to CrowdPulse in README/docs/UI title
- Confirm folder structure (`backend`, `frontend`, `edge`, `docs`)
- Create demo checklist document

**Done when**
- Project opens cleanly and README says CrowdPulse

---

### Day 2 — Backend health & API skeleton
**Do**
- Run FastAPI (`/health`, `/docs`)
- Verify twin/risk/decision/simulation routes respond
- Fix any startup errors

**Done when**
- `GET /health` = OK
- Swagger docs open

---

### Day 3 — Database + venue/zone model
**Do**
- Finalize tables: venues, zones, cameras, alerts, decisions
- Seed demo venue (4 zones A/B/C/D)
- API to fetch venue + zones

**Done when**
- Demo venue/zones load from API

---

### Day 4 — Frontend shell dashboard
**Do**
- Next.js pages: header, layout, panels
- Connect to backend API URL
- Show empty twin + risk cards placeholders

**Done when**
- UI loads at localhost:3000 and talks to API

---

### Day 5 — Video input module
**Do**
- Add API: upload CCTV video / select sample video
- Store video path locally (or MinIO later)
- Create “Process Video” button in UI

**Done when**
- User can upload a video file successfully

---

### Day 6 — YOLO detection on video
**Do**
- Integrate Ultralytics YOLO on uploaded video
- Extract person detections frame-wise
- Save count timeline (per N frames)

**Done when**
- Processing a sample video outputs person counts over time

---

### Day 7 — Tracking + basic zone assignment
**Do**
- Add ByteTrack (or YOLO built-in track)
- Map detections into 2–4 zones (simple grid/polygons)
- Compute zone counts

**Done when**
- Each zone gets a live/updating people count from video

---

## Week 2 — Analytics + Risk + ML Decisions

### Day 8 — Crowd analytics metrics
**Do**
- Compute density = count / area
- Estimate mean speed from tracks
- Estimate opposing flow / congestion proxy

**Done when**
- API returns metrics per zone for processed video

---

### Day 9 — DCRS risk engine wiring
**Do**
- Feed metrics into DCRS
- Output score + band (G/Y/O/R)
- Persist risk snapshots

**Done when**
- Zone B (or densest zone) shows Orange/Red correctly on dense clip

---

### Day 10 — Explainable alert module
**Do**
- Generate reason narrative from top features
- Show in API + UI expandable alert card

**Done when**
- Alert displays “why” (density/speed/exit pressure etc.)

---

### Day 11 — Gradient Boosting recommender integration
**Do**
- Ensure GB model trains/loads
- Produce ranked actions + confidence
- Attach actions to each alert

**Done when**
- High-risk zone returns actions like Open Exit / Deploy Guards / PA

---

### Day 12 — End-to-end API orchestration
**Do**
- One endpoint: `POST /api/v1/pipeline/run`
  - video → detect → metrics → risk → explain → recommend
- Return full JSON result for UI

**Done when**
- Single API call runs complete pipeline

---

### Day 13 — Dashboard twin map live update
**Do**
- Color zones by risk band
- Show DCRS number on each zone
- Auto-refresh after pipeline run

**Done when**
- After video process, map turns Y/O/R correctly

---

### Day 14 — Decision queue UI
**Do**
- Show recommended actions with confidence
- Accept / Dismiss buttons (store status)
- Display rationale text

**Done when**
- Panel can click accept on an action and status updates

---

## Week 3 — Simulation, Reports, Demo Polish

### Day 15 — What-if simulation backend
**Do**
- Scenario inputs: close exit, rainfall, VIP zone
- Recompute forecast/risk/actions
- Return predicted peak DCRS + congested zones

**Done when**
- Closing an exit increases predicted risk in response

---

### Day 16 — What-if UI
**Do**
- Form controls + run button
- Show simulation narrative and new recommendations

**Done when**
- Panel demo can run one what-if live

---

### Day 17 — Incident report module
**Do**
- Generate markdown summary (timeline, peak risk, actions)
- Optional Ollama if available; fallback template otherwise
- Download/view in UI

**Done when**
- Report generates after a processed event/video

---

### Day 18 — Historical hotspot + trends panel
**Do**
- Simple hotspot ranking by zone
- Trend chart for density/DCRS over processed frames

**Done when**
- Chart + hotspot list visible on dashboard

---

### Day 19 — Stability & error handling
**Do**
- Handle bad video, empty detections, API failures
- Loading spinners / progress for video processing
- Logging for pipeline stages

**Done when**
- App does not crash on common failures

---

### Day 20 — Sample CCTV dataset pack
**Do**
- Keep 2–3 sample videos (sparse / medium / dense)
- Precompute or quick-run results for backup demo
- Document which video to use in viva

**Done when**
- You have a reliable backup demo path if live processing is slow

---

### Day 21 — Performance pass
**Do**
- Process every Nth frame for speed
- Limit YOLO model size (yolo11n / yolov8n)
- Cache recommender model in memory

**Done when**
- One short clip processes in acceptable demo time (target < 1–2 min)

---

### Day 22 — Docs for panel
**Do**
- 1-page synopsis
- Architecture diagram
- Module-wise tech list
- Dataset explanation (public YOLO + synthetic GB labels)

**Done when**
- Docs ready to submit/show

---

### Day 23 — Full rehearsal #1
**Do**
- Run complete demo script start to end
- Note bugs/failures
- Fix top 5 issues

**Done when**
- Full flow works once without manual code fixes

---

### Day 24 — Full rehearsal #2 + viva Q&A prep
**Do**
- Practice answers:
  - Why Gradient Boosting?
  - Where dataset from?
  - Unique features vs normal counting?
  - Level A vs future pilot?
- Record a backup screen video of demo

**Done when**
- You can explain every module in simple words

---

### Day 25 — Final freeze
**Do**
- Freeze code
- Final README run instructions
- Clean demo account/data
- Sleep + confidence check

**Done when**
- Level A is presentation-ready

---

## Daily work rhythm (important)

For each day:
1. **Build** (2–4 hrs)
2. **Test** that day’s “Done when”
3. **Commit** progress
4. **Update** demo checklist

Do not jump ahead until that day’s Done when is true.

---

## Final Level A demo script (8–10 min)

1. Open CrowdPulse dashboard  
2. Upload dense CCTV clip  
3. Click Process  
4. Show twin map colors changing  
5. Open explainable alert  
6. Show Gradient Boosting recommendations + confidence  
7. Accept one action  
8. Run what-if (close exit)  
9. Generate incident report  
10. Conclude unique points

---

## What you need ready before Day 1

- Windows laptop with decent RAM (8GB+; 16GB better)
- Python + Node installed
- 2–3 crowd CCTV sample videos
- 1–2 hours/day minimum (more on weekends)

---

## After Level A

Only then start Level B (multi-camera operator pilot features).
