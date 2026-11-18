"""Dynamic Crowd Risk Score (DCRS) engine."""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.entities.crowd import RiskBand, RiskScore, ZoneMetrics


@dataclass(frozen=True)
class DCRSWeights:
    density_norm: float = 1.4
    speed_drop: float = 1.1
    opposing_flow: float = 1.2
    group_cohesion: float = 0.3
    abnormal_motion: float = 1.0
    exit_pressure: float = 1.3
    weather_factor: float = 0.5
    time_prior: float = 0.4
    historical_hotspot: float = 0.6
    emergency_flag: float = 2.0
    forecast_surge: float = 1.5
    bias: float = -2.2


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(x, 20.0), -20.0)))


def _clip(v: float, lo: float = 0.0, hi: float = 2.0) -> float:
    return max(lo, min(hi, v))


class DCRSEngine:
    """Multi-factor risk scoring with optional forecast horizon."""

    def __init__(self, weights: DCRSWeights | None = None, baseline_speed: float = 1.2):
        self.weights = weights or DCRSWeights()
        self.baseline_speed = baseline_speed

    def feature_vector(self, m: ZoneMetrics, capacity_density: float = 4.0) -> dict[str, float]:
        density_norm = m.density / max(capacity_density, 1e-6)
        speed_drop = 1.0 - (m.mean_speed / max(self.baseline_speed, 1e-6))
        speed_drop = _clip(speed_drop, 0.0, 1.0)
        return {
            "density_norm": _clip(density_norm),
            "speed_drop": speed_drop,
            "opposing_flow": _clip(m.opposing_flow, 0.0, 1.0),
            "group_cohesion": _clip(m.group_cohesion, 0.0, 1.0),
            "abnormal_motion": _clip(m.abnormal_motion, 0.0, 1.0),
            "exit_pressure": _clip(m.exit_pressure),
            "weather_factor": _clip(m.weather_factor, 0.0, 1.0),
            "time_prior": _clip(m.time_prior, 0.0, 1.0),
            "historical_hotspot": _clip(m.historical_hotspot, 0.0, 1.0),
            "emergency_flag": 1.0 if m.emergency_flag else 0.0,
            "forecast_surge": _clip(m.forecast_surge),
        }

    def score(self, features: dict[str, float]) -> tuple[float, dict[str, float]]:
        w = self.weights
        contributions: dict[str, float] = {}
        logit = w.bias
        for name, value in features.items():
            weight = getattr(w, name)
            contrib = weight * value
            contributions[name] = contrib
            logit += contrib
        dcrs = 100.0 * _sigmoid(logit)
        return dcrs, contributions

    @staticmethod
    def band(dcrs: float) -> RiskBand:
        if dcrs >= 80:
            return RiskBand.RED
        if dcrs >= 60:
            return RiskBand.ORANGE
        if dcrs >= 40:
            return RiskBand.YELLOW
        return RiskBand.GREEN

    def evaluate(
        self,
        metrics: ZoneMetrics,
        *,
        capacity_density: float = 4.0,
        horizon_minutes: int = 0,
        forecast_dcrs: float | None = None,
    ) -> tuple[RiskScore, dict[str, float], dict[str, float]]:
        features = self.feature_vector(metrics, capacity_density)
        dcrs, contributions = self.score(features)
        risk = RiskScore(
            zone_id=metrics.zone_id,
            timestamp=metrics.timestamp,
            dcrs=round(dcrs, 2),
            band=self.band(dcrs),
            horizon_minutes=horizon_minutes,
            forecast_dcrs=forecast_dcrs,
        )
        return risk, features, contributions
