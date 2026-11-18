# CrowdPulse

**An Intelligent Crowd Analytics and Decision Support Platform**

> CCTV in → risk + explanation + action recommendations out.  
> Not just crowd counting — decision support for authorities.

![status](https://img.shields.io/badge/level-A%20major%20project-0b1220)
![stack](https://img.shields.io/badge/stack-YOLO%20%7C%20Gradient%20Boosting%20%7C%20FastAPI%20%7C%20Next.js-3d8bfd)

---

## What CrowdPulse does

1. Detects people from CCTV / video (YOLO)
2. Computes zone crowd analytics
3. Calculates Dynamic Crowd Risk Score (DCRS)
4. Explains every alert
5. Recommends actions using **Gradient Boosting**
6. Shows live digital twin dashboard
7. Supports what-if simulation + incident report

---

## Repository structure

```
MAJORPROJECT/
├── backend/          # FastAPI + AI modules
├── frontend/         # Next.js ops dashboard
├── edge/             # Camera/video publisher
├── infra/            # Docker / K8s
├── docs/             # Design, plans, API
└── README.md
```

---

## Quick start

### Backend
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

- API: http://localhost:8000/docs  
- Login: http://localhost:3000/login  
- Dashboard: http://localhost:3000 (requires sign-in)

### Control-room login (Telangana demo accounts)

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `tsp.operator` | `Operator@TS2026` | Operator | Twin, risk, decisions, what-if, reports |
| `tsp.admin` | `Admin@TS2026` | Admin | Everything + CCTV upload / pipeline |
| `stadium.ops` | `Stadium@TS2026` | Operator | Stadium match-day desk (operator view) |

Change these passwords before any real police / stadium handover. JWT auth is **on by default** (`AUTH_REQUIRED=true`).

---

## Panel docs (Day 22)

Start here for submission / viva: [`docs/PANEL_PACK.md`](docs/PANEL_PACK.md)

- Synopsis · Architecture · Tech stack · Dataset

## Level A plan

See [`docs/LEVEL_A_25_DAY_PLAN.md`](docs/LEVEL_A_25_DAY_PLAN.md)

## Demo checklist

See [`docs/DEMO_CHECKLIST.md`](docs/DEMO_CHECKLIST.md)

---

## Tech highlight

| Module | Tech |
|---|---|
| Detection | YOLO |
| Recommendation | Gradient Boosting |
| Backend | FastAPI |
| Frontend | Next.js |
| DB | PostgreSQL + Redis |

## License

MIT
