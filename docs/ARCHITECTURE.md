# CrowdPulse Architecture (Level A — Panel)

Honest Level A view of what runs today (not future-only modules).

## System context

```mermaid
flowchart LR
  subgraph Operators
    OP[Control Room Operator]
    AD[Admin]
  end
  UI[Next.js Ops Console]
  API[FastAPI API + JWT]
  AI[Perception + DCRS + ERA + GB]
  DB[(SQLite / Postgres)]
  VID[Sample / Uploaded CCTV]

  OP --> UI
  AD --> UI
  UI --> API
  API --> AI
  API --> DB
  AD --> VID
  VID --> AI
  AI --> API
```

## Logical layers

```mermaid
flowchart TB
  subgraph Presentation
    FE[Next.js Dashboard]
    LOGIN[JWT Login]
  end
  subgraph API
    REST[REST /api/v1]
    AUTH[Auth RBAC]
  end
  subgraph Application
    UC[Use-cases: process video, pipeline, evaluate risk]
  end
  subgraph AI
    DET[Detector YOLO-n / HOG]
    TRK[Centroid-IoU Tracker]
    ZN[Zone assign + analytics]
    DCRS[DCRS Engine]
    ERA[Explainable Risk Attributor]
    GB[Gradient Boosting CDSE]
    SIM[What-if simulator]
    REP[Incident reporter]
  end
  subgraph Data
    SQL[(venues zones cameras alerts decisions videos)]
    TWIN[In-memory twin store]
    FILES[uploads/samples]
  end

  FE --> LOGIN --> REST
  REST --> AUTH --> UC
  UC --> DET --> TRK --> ZN --> DCRS --> ERA --> GB
  UC --> SIM
  UC --> REP
  UC --> SQL
  UC --> TWIN
  DET --> FILES
```

## Pipeline sequence

```mermaid
sequenceDiagram
  participant Admin
  participant UI
  participant API
  participant CV as Detect/Track
  participant Risk as DCRS+ERA+GB
  participant Twin

  Admin->>UI: Sample Dense / Process
  UI->>API: POST /pipeline/run (JWT)
  API->>CV: frames (stride N)
  CV-->>API: zone counts + timeline
  API->>Risk: evaluate + recommend
  Risk-->>API: DCRS, explanation, actions
  API->>Twin: update metrics/alerts
  API-->>UI: twin snapshot
  UI-->>Admin: map colors + decision queue
```

## Module map (repo)

| Path | Responsibility |
|------|----------------|
| `frontend/` | Ops UI: twin, risk, decisions, CCTV, what-if, analytics, report |
| `backend/app/api/` | REST routes + JWT deps |
| `backend/app/application/` | Use-cases (pipeline, process video, evaluate risk) |
| `backend/app/ai/perception/` | Detect, track, zones, analytics |
| `backend/app/ai/risk/` | DCRS |
| `backend/app/ai/xai/` | ERA |
| `backend/app/ai/decision/` | GB recommender + safety filter |
| `backend/app/ai/simulation/` | What-if |
| `backend/app/ai/reporting/` | Incident markdown (Ollama optional) |
| `backend/app/infrastructure/` | DB, seed, twin store, video storage |
| `edge/` | Future / optional edge publisher (Level B) |

## Security
- JWT login (`tsp.operator` / `tsp.admin`)  
- Operator cannot run ingest/pipeline; Admin can  
- Secrets via env (`SECRET_KEY`, `AUTH_REQUIRED`)

## Scale path (Level B — not claimed as done)
Multi-camera fusion, Timescale metrics, Redis streams, ONNX edge nodes — see `FUTURE_SCOPE.md` / design doc.
