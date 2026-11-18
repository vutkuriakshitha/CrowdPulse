# CrowdPulse — Project Design Document

## 1. Unique Project Title

**CrowdPulse: An Intelligent Crowd Analytics and Decision Support Platform**

Short name: **CrowdPulse**  
Tagline: *From crowd counting to decision support.*

---

## 2. IEEE-Level Abstract

Large-scale gatherings continue to produce preventable crush and stampede disasters despite widespread CCTV deployment. Existing computer-vision systems predominantly perform reactive crowd counting or short-horizon density alerts and rarely close the operational loop from perception to explainable decision support. This paper presents **VigilantTwin**, a production-oriented cognitive crowd governance platform that fuses multi-camera edge perception, spatiotemporal graph forecasting, and a digital-twin control plane. Person detections from overlapping cameras are de-duplicated via geometric and appearance fusion, then aggregated into a venue zone graph. A hybrid **Temporal Fusion Transformer + Graph Neural Network** forecasts zone occupancy, flow, and a multi-factor **Dynamic Crowd Risk Score (DCRS)** five to ten minutes ahead. Every alert is accompanied by an **Explainable Risk Attribution (ERA)** record listing contributing factors (density, speed decay, opposing flow, exit availability, weather, historical hotspot prior). A **Cognitive Decision Support Engine (CDSE)** maps risk states to actionable interventions (gate control, guard redeployment, PA messages, zone redirection). Authorities can run **what-if simulations** (exit closure, rainfall, VIP ingress) against the live twin, while a resource optimizer proposes evacuation paths and emergency asset placement. After events, a local GenAI module synthesizes timeline-aware PDF incident reports. Unlike detection-centric IEEE systems, VigilantTwin unifies predictive risk, explainability, digital twinning, multi-camera fusion, decision support, and simulation into one scalable edge–cloud architecture.

**Keywords:** crowd risk forecasting, digital twin, multi-camera fusion, explainable AI, decision support, graph neural networks, stampede prevention, smart surveillance.

---

## 3. Novel Contributions (8 Core Innovations)

| # | Innovation | Why it is rare |
|---|---|---|
| C1 | **Multi-horizon DCRS** (5–10 min) using density, speed, flow conflict, exits, weather, history | Most systems are reactive or ≤2 min density-only |
| C2 | **Cognitive Decision Support Engine** with rule+ML action cards | Papers stop at “High Density” alerts |
| C3 | **Live venue Digital Twin** with Green→Red zones + predictive heatmaps | Twins often static / visualization-only |
| C4 | **Multi-camera geometric–appearance fusion** anti-double-count | Many YOLO papers use single camera |
| C5 | **ST-GNN + TFT crowd flow forecasting** on zone graph | Forecast models rarely embedded in ops twin |
| C6 | **Explainable Risk Attribution (ERA)** on every alert | XAI rarely shipped with live CCTV risk |
| C7 | **Online what-if scenario planner** on live twin state | Usually offline architectural simulation |
| C8 | **Resource OR + GenAI after-action reports + historical hotspot learning** | Almost never co-deployed with C1–C7 |

---

## 4. Research Gap Statement

Prior IEEE work (2023–2025) advances YOLO counting, short LSTM density forecasts, multi-modal sensing, or conceptual digital twins in isolation. **No open, end-to-end system jointly delivers multi-camera de-duplicated perception, multi-factor multi-horizon risk, explainable alerts, cognitive action recommendations, live what-if simulation, resource optimization, and GenAI incident reporting on a shared zone ontology.** VigilantTwin fills this governance gap.

---

## 5. System Architecture (Logical Layers)

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation: Next.js Ops Dashboard + Mobile Alert Client      │
├─────────────────────────────────────────────────────────────────┤
│  API Gateway: FastAPI (REST + WebSocket) + Auth (JWT/RBAC)      │
├─────────────────────────────────────────────────────────────────┤
│  Application Services (Clean Architecture Use-Cases)            │
│  Twin | Risk | Decision | Simulation | Analytics | Reports      │
├─────────────────────────────────────────────────────────────────┤
│  AI Services                                                    │
│  Fusion | Forecasting (TFT+GNN) | DCRS | ERA/XAI | CDSE | OR    │
├─────────────────────────────────────────────────────────────────┤
│  Edge Perception Cluster                                        │
│  Camera → YOLOv11/ONNX → ByteTrack → Redis Stream publish       │
├─────────────────────────────────────────────────────────────────┤
│  Data Plane                                                     │
│  PostgreSQL+TimescaleDB | Redis | MinIO | Optional Kafka        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Module Diagram

```
edge/
  detector     → person detection (YOLOv11 / ONNX Runtime)
  tracker      → multi-object tracking (ByteTrack)
  publisher    → publishes detections to Redis Streams

backend/ai/
  fusion       → multi-cam de-duplication + zone mapping
  forecasting  → TFT + ST-GNN zone flow forecast
  risk         → Dynamic Crowd Risk Score (DCRS)
  xai          → Explainable Risk Attribution
  decision     → Cognitive Decision Support Engine
  simulation   → what-if scenario runner
  reporting    → GenAI PDF incident reports

backend/application/
  use_cases    → orchestrate domain + AI ports

frontend/
  digital-twin | risk | cameras | analytics | simulation | reports
```

---

## 7–8 / 20. Database Schema (Summary)

See `docs/DATABASE.md` and SQLAlchemy models. Core tables:

- `venues`, `zones`, `cameras`, `camera_zone_overlaps`
- `detections` (hypertable), `tracks`, `fused_counts` (hypertable)
- `zone_metrics` (hypertable), `risk_scores` (hypertable)
- `risk_explanations`, `alerts`, `decisions`, `decision_actions`
- `simulations`, `simulation_results`
- `resources`, `resource_assignments`
- `events`, `historical_hotspots`
- `incident_reports`, `users`, `audit_logs`

---

## 9. Frontend Design

- **Dark ops console** with MapLibre venue twin (not purple SaaS aesthetic)
- Live zone choropleth (G/Y/O/R), flow arrows, predictive heatmap overlay
- Risk cards with ERA expandable reasons
- Decision action queue (accept / dismiss / escalate)
- What-if drawer (exit close, weather, VIP)
- Camera mosaic + fused count badge
- Historical hotspot compare + GenAI report viewer
- Typography: **IBM Plex Sans** + **IBM Plex Mono** (ops clarity)

---

## 10. Backend Design (Clean Architecture)

```
api → application/use_cases → domain ← infrastructure adapters
                              ↑
                           ai ports
```

Dependencies point inward. Frameworks and DB are infrastructure details.

---

## 11. AI Pipeline

1. Edge: frame → YOLO → ByteTrack → `{camera_id, track_id, bbox, conf, ts}`
2. Cloud Fusion: homography + ReID embedding → global person IDs → zone counts
3. Metrics: density, mean speed, flow vectors, congestion index
4. Forecast: zone graph + TFT → occupancy/flow @ t+5..t+10 min
5. DCRS: weighted multi-factor score → risk band
6. ERA: feature contributions + natural-language reason bundle
7. CDSE: rules + ML ranker → action cards
8. Optional OR: evacuation / guard / medical placement
9. Persist + WebSocket fan-out to twin dashboard

---

## 12. Model Selection (Open Source)

| Stage | Model | Why |
|---|---|---|
| Detection | Ultralytics YOLOv11 / YOLOv8-m (ONNX) | Speed/accuracy for edge |
| Tracking | ByteTrack | Robust MOT, open |
| Re-ID (optional) | OSNet (torchreid) | Lightweight cross-cam |
| Density fallback | CSRNet / lightweight density head | Extreme occlusion |
| Temporal forecast | Temporal Fusion Transformer (PyTorch Forecasting) | Multi-horizon + covariates |
| Spatial forecast | GraphSAGE / GAT (PyTorch Geometric) | Zone topology |
| XAI | Captum Integrated Gradients + rule attribution | Alert explainability |
| Decision ranker | LightGBM / XGBoost | Fast tabular action scoring |
| GenAI reports | Ollama + Llama 3.1 / Mistral | Local, open, offline-capable |
| Simulation | NetworkX + continuum/flow heuristics | Fast what-if |

---

## 13. Folder Structure

See repository root layout (monorepo).

---

## 14. Technology Stack (Open Source Only)

| Layer | Tech |
|---|---|
| Edge | Python, OpenCV, Ultralytics, ONNX Runtime, ByteTrack |
| API | FastAPI, Pydantic v2, Uvicorn, Celery |
| DB | PostgreSQL 16, TimescaleDB, Redis 7, MinIO |
| Messaging | Redis Streams (Kafka optional) |
| AI | PyTorch, PyG, pytorch-forecasting, Captum, LightGBM, Ollama |
| Frontend | Next.js 14, TypeScript, Tailwind, MapLibre GL, Zustand, Recharts |
| Auth | Keycloak or JWT + RBAC |
| Observability | Prometheus, Grafana, OpenTelemetry |
| Deploy | Docker Compose, Kubernetes (k3s/k8s), Nginx |
| CI | GitHub Actions |

---

## 15. Deployment Architecture

```
[Cameras] → [Edge Node GPU/CPU] → Redis Streams
                                      ↓
                              [Fusion Worker]
                                      ↓
                    [Forecast/Risk/Decision Workers]
                                      ↓
                         PostgreSQL + Redis + MinIO
                                      ↓
                         FastAPI + WebSocket Gateway
                                      ↓
                    Ops Dashboard / Mobile Push (FCM OSS alt: ntfy)
```

---

## 16–18. UML / Sequence / ER

Mermaid sources in `docs/diagrams/`. Rendered summaries:

- **UML components**: Edge, Fusion, Risk, Twin, CDSE, UI
- **Sequence**: Detection → Fusion → DCRS → ERA → Alert → Decision → UI
- **ER**: venues–zones–cameras–metrics–risks–decisions–simulations–reports

---

## 19. Risk Prediction Algorithm (DCRS)

See `backend/app/ai/risk/dcrs.py` and `docs/DCRS_ALGORITHM.md`.

```
DCRS(z,t) = σ( Σ w_i · φ_i(z,t, t+Δ) )
φ = {density_norm, speed_drop, opposing_flow, group_cohesion,
     abnormal_motion, exit_pressure, weather_factor,
     time_prior, historical_hotspot, emergency_flag, forecast_surge}
Band: Green <40 | Yellow 40–60 | Orange 60–80 | Red ≥80
Alert if band≥Orange OR forecast_band(t+10)≥Orange
```

---

## 21. Sprint Plan (12 weeks)

| Sprint | Weeks | Focus |
|---|---|---|
| S1 | 1–2 | Venue ontology, DB, camera ingest stub, CI |
| S2 | 3–4 | Edge YOLO+ByteTrack, Redis streams |
| S3 | 5–6 | Multi-cam fusion + zone metrics |
| S4 | 7–8 | DCRS + ERA + alerts WebSocket |
| S5 | 9–10 | TFT+GNN forecast + Digital Twin UI |
| S6 | 11 | CDSE + what-if + resource OR |
| S7 | 12 | GenAI reports, load test, paper experiments |

---

## 22–23. GitHub Structure & README

Root README is the entrypoint; modules documented under `/docs`.

---

## 24. Future Scope

- Multimodal WiFi/BLE sensing fusion
- Drone overhead calibration
- Federated learning across venues
- Formal verification of CDSE safety constraints
- VR command-center twin
- National emergency agency interoperability (CAP alerts)
