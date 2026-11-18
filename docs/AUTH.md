# CrowdPulse Control-Room Authentication

Designed for **Telangana State Police / stadium venue control rooms** (Level A major-project scope).

## Roles

| Role | Who | Can do |
|------|-----|--------|
| `operator` | Control room / match-day desk | View twin, risk, alerts, GB recommendations, what-if, reports, cameras |
| `admin` | Control room administrator | Everything above + video upload, process, one-click pipeline, twin reset-metrics |

## Flow

1. User opens `/login`
2. `POST /api/v1/auth/login` → JWT (`Bearer`)
3. Frontend stores token + user in `localStorage`
4. All `/api/v1/*` (except `/auth/login`) require JWT
5. Admin-only writes: upload / process / pipeline / reset-metrics

## Seeded demo users

See root `README.md`. Seeded on backend startup via `seed_control_room_users()`.

## Config

| Env | Default | Meaning |
|-----|---------|---------|
| `AUTH_REQUIRED` | `true` | Enforce JWT on ops APIs |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | 8-hour shift token |
| `SECRET_KEY` | (change me) | JWT signing key |

Set `AUTH_REQUIRED=false` only for local emergency bypass — never for handover demos.

## Verify scripts

`day2_smoke_test.py`, `day3_verify.py`, and `day13_verify.py` login via `scripts/cp_http.py`.  
Other day scripts: either update them to use `cp_http`, or run with `AUTH_REQUIRED=false` temporarily.
