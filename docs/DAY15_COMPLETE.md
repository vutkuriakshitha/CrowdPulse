# Day 15 Completion Log — CrowdPulse Level A

**Date:** 2026-07-16  
**Status:** COMPLETE

## Done today
1. **What-if simulator hardened** (`what_if.py`)
   - Close exit only stresses zones that use that exit (+ adjacent spillover)
   - Rainfall / VIP / hold-ingress perturbations kept
   - Returns `baseline_peak_dcrs`, `dcrs_delta`, `zone_risks`, richer narrative
2. **API**
   - `POST /api/v1/simulation/what-if` persists to `simulations` table
   - `GET /api/v1/simulation/recent` lists recent runs
3. **UI (minimal)** — What-If panel shows baseline + Δ DCRS
4. Verify: `backend/scripts/day15_verify.py`

## Verified
```
[PASS] baseline sim …
[PASS] close Gate-C raises peak …
[PASS] Gate-C removed from effective exits …
[PASS] rainfall / VIP sims …
Day 15 verification OK
```

## Done when (plan)
Closing an exit increases predicted risk vs baseline — **met**.

## Next — Day 16
What-if UI polish (form UX, narrative, recommendation list).
