# CrowdPulse — Dataset Explanation (Panel / Viva)

## 1. Person detection
| Item | Detail |
|------|--------|
| Source | **Public pretrained weights** — Ultralytics YOLOv8n trained on COCO (person class = 0) |
| Fallback | OpenCV HOG + default people SVM (no extra dataset download) |
| Our labeling | We do **not** train a custom detector for Level A |
| Viva line | “Detection uses public YOLO person weights; if YOLO is unavailable we fall back to OpenCV HOG.” |

## 2. Action recommendation (Gradient Boosting)
| Item | Detail |
|------|--------|
| Features | DCRS, density, speed drop, opposing flow, exit pressure, weather, hotspot prior, etc. |
| Labels | **Synthetic multi-label actions** generated from expert-style rules over feature ranges |
| Size | Thousands of synthetic scenarios (see `ML_RECOMMENDER.md` benchmark ~3000 samples) |
| Why synthetic | Real labeled “operator decisions” need venue SOPs; synthetic lets us train/compare models ethically for a college project |
| Safety | Rules only **filter** unsafe actions after ML ranking |
| Viva line | “GB is trained on synthetic multi-factor crowd-risk scenarios with rule-derived action labels; we benchmarked GB vs Random Forest and selected GB.” |

## 3. Demo CCTV clips
| Clip | Role |
|------|------|
| `sparse_crowd.mp4` | Low density |
| `medium_crowd.mp4` / `synthetic_crowd.mp4` | Balanced |
| `dense_crowd.mp4` | High density — **primary viva clip** |

Generated procedurally (OpenCV) so the demo is reproducible without copyrighted CCTV. Guide: `SAMPLE_CCTV_PACK.md`.

## 4. Venue / topology
Seeded demo venue **Aether Arena** (zones A–D, exits, cameras) in SQLite — schema-backed, not hard-coded UI-only.

## Honest limitation
We do **not** claim a private Telangana Police CCTV corpus. The product path is: public detector + synthetic decision labels + venue seed + synthetic/demo video; real CCTV can be uploaded by Admin when available.
