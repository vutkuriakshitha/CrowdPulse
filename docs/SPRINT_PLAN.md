# 12-Week Sprint Plan

| Sprint | Weeks | Deliverables | Exit Criteria |
|---|---|---|---|
| S1 Foundation | 1–2 | Monorepo, DB schema, venue ontology, CI, demo twin API | `/twin/snapshot` works |
| S2 Edge Perception | 3–4 | YOLO+ByteTrack edge publisher, Redis streams | Detections flowing |
| S3 Fusion | 5–6 | Homography calib tool, anti-double-count, zone metrics | Fused counts stable |
| S4 Risk + XAI | 7–8 | DCRS, ERA, alerts, WebSocket | Orange/Red alerts explainable |
| S5 Forecast + Twin UI | 9–10 | Forecaster horizons, Next.js twin map, trends | 5–10 min forecast visible |
| S6 Decisions + Sim | 11 | CDSE, what-if, resource optimizer | Action cards + sim accepted by ops |
| S7 Reports + Eval | 12 | GenAI PDF, load test, paper experiments on public datasets | IEEE draft metrics ready |

## Dataset Plan for Publication
- Train/eval detection: JHU-CROWD++, CrowdHuman
- Tracking: MOT20 subset / custom venue tracks
- Risk labels: synthetic near-miss windows + historical event reconstructions
- Ablations: density-only vs DCRS; single-cam vs fusion; w/ vs w/o forecast surge
