# CrowdPulse — Module-wise Technology List (Level A)

| Module | Technology | Role in system |
|--------|------------|----------------|
| Ops UI | Next.js 14, React, Tailwind, Recharts | Control-room dashboard |
| Auth | JWT (PyJWT), bcrypt, role RBAC | Operator / Admin access |
| API | FastAPI, Pydantic, Uvicorn | REST APIs, validation |
| Architecture | Clean Architecture use-cases | Replaceable modules |
| Persistence | SQLAlchemy async, SQLite (Postgres-ready) | Venues, zones, videos, alerts, reports |
| Twin | In-memory twin store + DB topology | Live zone metrics / alerts |
| Detection | Ultralytics YOLOv8n (optional) / OpenCV HOG | Person detection |
| Tracking | Centroid + IoU tracker | Multi-person tracks |
| Zone analytics | OpenCV + NumPy | Density, speed, opposing flow |
| Risk | Custom DCRS (weighted logistic / sigmoid) | Score + G/Y/O/R band |
| Explainability | ERA feature contributions | Why risk is high |
| Recommendations | scikit-learn GradientBoostingClassifier | Ranked actions + confidence |
| Safety layer | Deterministic constraints | e.g. never close last exit |
| What-if | Perturb twin → re-score | Close exit / rain / VIP |
| Reports | Template markdown (+ optional Ollama) | After-action summary |
| Demo video | OpenCV-generated sparse/medium/dense MP4 | Reliable viva clips |
| Config | pydantic-settings, `.env` | No hardcoded secrets |

## Key libraries
**Backend:** `fastapi`, `uvicorn`, `sqlalchemy`, `aiosqlite`, `opencv-python-headless`, `numpy`, `scikit-learn`, `PyJWT`, `bcrypt`, `httpx`  
**Frontend:** `next`, `react`, `recharts`, `tailwindcss`

## What we deliberately did *not* claim as Level A complete
- ByteTrack / multi-camera fusion  
- TFT + GNN forecasting as production path  
- Full TimescaleDB hypertables in runtime  
- Live RTSP viewer (cameras are seeded metadata)

These remain design / Level B stretch items.
