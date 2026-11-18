"""Explainable Risk Attribution (ERA)."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.crowd import FeatureContribution, RiskExplanation


FEATURE_LABELS = {
    "density_norm": "Crowd density vs safe capacity",
    "speed_drop": "Walking speed drop vs baseline",
    "opposing_flow": "Opposing / conflicting movement",
    "group_cohesion": "Dense group formation",
    "abnormal_motion": "Abnormal motion / turbulence",
    "exit_pressure": "Exit queue pressure",
    "weather_factor": "Adverse weather impact",
    "time_prior": "Event-phase congestion prior",
    "historical_hotspot": "Historical hotspot pattern",
    "emergency_flag": "Active emergency event",
    "forecast_surge": "Predicted surge in next horizon",
}


class ExplainableRiskAttributor:
    """Builds human-readable explanations for DCRS alerts."""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def explain(
        self,
        *,
        risk_id: UUID,
        zone_id: UUID,
        dcrs: float,
        features: dict[str, float],
        contributions: dict[str, float],
        weights: dict[str, float],
    ) -> RiskExplanation:
        items: list[FeatureContribution] = []
        for name, contrib in contributions.items():
            items.append(
                FeatureContribution(
                    feature=name,
                    value=round(features.get(name, 0.0), 3),
                    weight=round(weights.get(name, 0.0), 3),
                    contribution=round(contrib, 3),
                )
            )
        items.sort(key=lambda x: x.contribution, reverse=True)
        top = items[: self.top_k]
        lines = [f"Risk Score = {dcrs:.0f}", "", "Reason:"]
        for c in top:
            label = FEATURE_LABELS.get(c.feature, c.feature)
            lines.append(f"- {label} (value={c.value}, impact={c.contribution:+.2f})")
        return RiskExplanation(
            risk_id=risk_id,
            zone_id=zone_id,
            dcrs=dcrs,
            contributions=items,
            narrative="\n".join(lines),
        )

    @staticmethod
    def top_factors(explanation: RiskExplanation, k: int = 5) -> list[dict]:
        """API-friendly top drivers for expandable alert cards."""
        rows = []
        for c in explanation.contributions[:k]:
            rows.append(
                {
                    "feature": c.feature,
                    "label": FEATURE_LABELS.get(c.feature, c.feature),
                    "value": c.value,
                    "weight": c.weight,
                    "contribution": c.contribution,
                }
            )
        return rows
