"""Crowd analytics derived from tracked trajectories."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np


@dataclass
class TrackSample:
    track_id: int
    zone_code: str | None
    x: float
    y: float
    time_sec: float
    confidence: float


def compute_zone_analytics(
    samples: list[TrackSample],
    *,
    zone_areas: dict[str, float],
    latest_counts: dict[str, int],
    pixels_per_meter: float = 25.0,
) -> dict[str, dict]:
    """Compute per-zone density, speed, opposing flow, congestion proxies."""
    by_track: dict[int, list[TrackSample]] = defaultdict(list)
    for s in samples:
        by_track[s.track_id].append(s)

    # per-zone accumulators
    speeds: dict[str, list[float]] = defaultdict(list)
    headings: dict[str, list[float]] = defaultdict(list)
    confs: dict[str, list[float]] = defaultdict(list)
    dwell: dict[str, list[float]] = defaultdict(list)

    for tid, seq in by_track.items():
        seq = sorted(seq, key=lambda s: s.time_sec)
        if len(seq) < 2:
            if seq and seq[0].zone_code:
                confs[seq[0].zone_code].append(seq[0].confidence)
            continue

        # segment-wise metrics
        zone_time: dict[str, float] = defaultdict(float)
        for a, b in zip(seq, seq[1:]):
            dt = max(b.time_sec - a.time_sec, 1e-3)
            dist_px = float(np.hypot(b.x - a.x, b.y - a.y))
            speed_mps = (dist_px / pixels_per_meter) / dt
            heading = float(np.arctan2(b.y - a.y, b.x - a.x))
            zc = b.zone_code or a.zone_code
            if not zc:
                continue
            speeds[zc].append(max(0.0, min(speed_mps, 3.5)))
            headings[zc].append(heading)
            confs[zc].append(b.confidence)
            zone_time[zc] += dt
        for zc, t in zone_time.items():
            dwell[zc].append(t)

    out: dict[str, dict] = {}
    for code, area in zone_areas.items():
        count = int(latest_counts.get(code, 0))
        density = count / max(area, 1e-6)
        sp = speeds.get(code, [])
        hd = headings.get(code, [])
        mean_speed = float(np.mean(sp)) if sp else 0.0
        # opposing flow: fraction of heading pairs that disagree > 90 deg
        opposing = 0.0
        if len(hd) >= 2:
            arr = np.asarray(hd)
            # circular variance proxy via resultant length
            mean_c = np.mean(np.cos(arr))
            mean_s = np.mean(np.sin(arr))
            R = float(np.hypot(mean_c, mean_s))
            opposing = float(np.clip(1.0 - R, 0.0, 1.0))
        # congestion: high density + low speed
        congestion = float(np.clip((density / 4.0) * (1.0 - min(mean_speed / 1.2, 1.0)), 0.0, 1.0))
        # abnormal motion: speed variance
        abnormal = float(np.clip(np.std(sp) / 1.0, 0.0, 1.0)) if len(sp) >= 2 else 0.0
        # group cohesion proxy: inverse of spatial spread is hard here; use dwell consistency
        cohesion = float(np.clip(np.mean(dwell[code]) / 5.0, 0.0, 1.0)) if dwell.get(code) else 0.0
        # exit pressure proxy: density * opposing
        exit_pressure = float(np.clip(density / 3.0 + opposing * 0.5, 0.0, 2.0))

        out[code] = {
            "count": count,
            "density": round(density, 4),
            "mean_speed": round(mean_speed, 3),
            "opposing_flow": round(opposing, 3),
            "congestion_index": round(congestion, 3),
            "abnormal_motion": round(abnormal, 3),
            "group_cohesion": round(cohesion, 3),
            "exit_pressure": round(exit_pressure, 3),
            "avg_confidence": round(float(np.mean(confs[code])), 3) if confs.get(code) else 0.0,
            "speed_samples": len(sp),
        }
    return out
