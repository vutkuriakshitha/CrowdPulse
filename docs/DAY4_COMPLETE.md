# Day 4 Completion Log — CrowdPulse Level A

**Date:** 2026-07-15  
**Status:** COMPLETE

## Done today
1. Production-style **Operations Console** shell (`AppShell`)
2. Live status pills: API / DB / Venue
3. Typed API client with health + demo venue + twin snapshot
4. Loading + error states for offline backend
5. Camera network strip from DB-backed venue cameras
6. Connected dashboard panels to live backend
7. `.env.local` → `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`
8. CORS updated for localhost + 127.0.0.1

## Verified
- Frontend: `GET http://127.0.0.1:3000` → **200** (contains CrowdPulse)
- Backend health: ok, database venues=1
- Next.js ready on port 3000

## How to run
```bash
# terminal 1
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000

# terminal 2
cd frontend
npm run dev
```

Open: http://localhost:3000

## Day 4 exit criteria
- [x] UI loads at localhost:3000
- [x] UI talks to API (health + venue + twin)

## Next — Day 5
Video upload module for CCTV footage ingest.
