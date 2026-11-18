# REST & WebSocket APIs — CrowdPulse

Base URL: `http://localhost:8000`

## Health & catalog
- `GET /health`
- `GET /api/v1/` — module catalog
- `GET /docs` — Swagger UI

## Venues (DB-backed)
- `GET /api/v1/venues/`
- `GET /api/v1/venues/demo`
- `GET /api/v1/venues/{venue_id}`
- `GET /api/v1/venues/{venue_id}/zones`
- `GET /api/v1/venues/{venue_id}/cameras`

## Pipeline (one-click)
- `GET /api/v1/pipeline/status` — flow catalog
- `POST /api/v1/pipeline/run` — video → detect → track → analytics → DCRS → ERA → GB → twin
```json
{
  "video_id": null,
  "sample_filename": "synthetic_crowd.mp4",
  "use_latest_upload": false,
  "frame_stride": 5,
  "max_frames": 40,
  "include_twin": true
}
```

## Videos (CCTV ingest + detection)
- `POST /api/v1/videos/upload` (multipart form: `file`, optional `notes`)
- `GET /api/v1/videos/`
- `GET /api/v1/videos/detector/status`
- `GET /api/v1/videos/{video_id}`
- `POST /api/v1/videos/{video_id}/queue`
- `POST /api/v1/videos/{video_id}/process` — detect + track + zone analytics + **DCRS**
  - Returns `zone_summary`, `risk_by_zone`, `peak_dcrs` / `peak_zone` / `peak_band`, `alerts`
  - Updates twin metrics + live risk; persists `risk_snapshots` (+ alerts if Orange+)
- `GET /api/v1/videos/{video_id}/detections` — includes `zone_summary` + `zone_analytics` in summary
- `GET /api/v1/videos/samples`
- `POST /api/v1/videos/samples/register`

## Digital Twin
- `GET /api/v1/twin/snapshot` — full twin state with risk + explanations + alerts
- `GET /api/v1/twin/zones`
- `POST /api/v1/twin/reset-metrics` — restore seeded demo densities + re-run DCRS
- `WS /ws/twin` — push snapshot every 3s

## Risk
- `POST /api/v1/risk/evaluate` — run DCRS on current twin metrics
- `GET /api/v1/risk/alerts?limit=20` — alerts with ERA `explanation` (`narrative`, `contributions`, `top_labels`)
- `GET /api/v1/risk/snapshots?limit=40&video_id=` — persisted DCRS + explanation payloads

## Decisions
- `GET /api/v1/decisions/recommender/status` — Gradient Boosting model health + importances
- `GET /api/v1/decisions`
- `POST /api/v1/decisions/ack`
```json
{ "alert_id": "...", "action_type": "open_exit", "status": "accepted" }
```

## Simulation
- `POST /api/v1/simulation/what-if`
```json
{
  "name": "Close Gate-C + rain",
  "close_exits": ["Gate-C"],
  "rainfall_mm_h": 12,
  "vip_zone": "B",
  "hold_ingress": false,
  "horizon_minutes": 10
}
```

## Analytics
- `GET /api/v1/analytics/hotspots` — historical hotspot + live density/speed/opposing/congestion
- `GET /api/v1/analytics/trends`

## Reports
- `POST /api/v1/reports/incident`
