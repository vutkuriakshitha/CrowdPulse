# CrowdPulse Sample CCTV Pack (Day 20)

Location: `backend/data/uploads/samples/`

| File | Density | People (synthetic) | Use when |
|------|---------|----------------------|----------|
| `sparse_crowd.mp4` | Sparse | ~3 | Show green/yellow risk, calm ops |
| `medium_crowd.mp4` | Medium | ~8 | Default / balanced demo |
| `dense_crowd.mp4` | Dense | ~18 | **Viva primary** — orange/red + GB actions |
| `synthetic_crowd.mp4` | Medium alias | ~8 | One-click pipeline default |

## Generate / refresh clips

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts\make_sample_pack.py
```

## Viva recommendation

1. **Preferred live path:** Admin → One-Click Full Pipeline (uses sample automatically)  
   or register `dense_crowd.mp4` and Process.
2. **If processing is slow:**  
   - Admin → `POST /api/v1/twin/reset-metrics` (instant hot Zone B)  
   - Show Accept/Dismiss, what-if, report  
   - Optional: open precomputed `backend/data/demo_backup/dense_pipeline_result.json`

## Precompute backup JSON

Backend must be running + auth:

```powershell
python scripts\precompute_demo_backup.py
```

## Register a sample via API

```json
POST /api/v1/videos/samples/register
{ "filename": "dense_crowd.mp4" }
```
