# CrowdPulse — One-Page Project Synopsis

**Title:** CrowdPulse: An Intelligent Crowd Analytics and Decision Support Platform  

**Domain:** Smart surveillance / crowd safety for stadiums & public venues (Telangana control-room oriented demo)

## Problem
CCTV alone counts people. Authorities still lack a closed loop from **detection → risk → explanation → recommended action**. Crush and congestion events remain preventable with better decision support.

## Solution
CrowdPulse ingests CCTV video, detects and tracks people, maps them to venue zones, computes a **Dynamic Crowd Risk Score (DCRS)** with explainable factors, and ranks interventions using **Gradient Boosting**. Operators work in a secured ops console with what-if simulation and after-action reports.

## End-to-end flow
```
CCTV video → Detect (YOLO nano / HOG) → Track → Zone analytics
→ DCRS + ERA explain → GB recommendations → Digital twin dashboard
→ Accept/Dismiss → What-if → Incident report
```

## Novelty (what to emphasize)
| Point | CrowdPulse |
|-------|------------|
| Not only counting | Risk score + band (G/Y/O/R) |
| Explainability | ERA narrative + feature contributions |
| Decision support | Gradient Boosting action ranking + safety filter |
| Operator loop | Login, Accept/Dismiss, what-if, report |
| Venue twin | Live zone map colored by risk |

## Stack (Level A implemented)
- **Frontend:** Next.js ops console  
- **Backend:** FastAPI, Clean Architecture use-cases  
- **Auth:** JWT + roles (Operator / Admin)  
- **DB:** SQLite (Postgres-ready)  
- **CV:** YOLOv8n (optional) / OpenCV HOG; centroid-IoU tracker  
- **ML:** scikit-learn Gradient Boosting recommender  
- **Risk:** DCRS + Explainable Risk Attribution  

## Dataset
- **Detection:** Public pretrained YOLO person weights (COCO person class) or HOG people detector  
- **Recommender:** Synthetic multi-factor crowd-risk scenarios with rule-derived multi-label actions (benchmarked GB vs RF)  
- **Demo video:** Synthetic sparse/medium/dense CCTV-like clips  

## Roles
- **Operator** — twin, risk, decisions, what-if, report  
- **Admin** — all of the above + CCTV ingest / pipeline  

## Maturity note
Level A = **venue pilot / panel demo** (single venue, file/CCTV clip ingest). Not full city-scale multi-camera production; architecture leaves room for Level B (multi-cam fusion, Postgres/Timescale).

## Demo (≤10 min)
Login → twin map → Sample Dense / pipeline → risk colors + explain → Accept action → what-if close exit → generate report.
