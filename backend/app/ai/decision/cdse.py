"""Cognitive Decision Support Engine (CDSE) — ML-first recommendations.

Primary intelligence: Gradient Boosting multi-label action recommender
(benchmarked over Random Forest — see docs/ML_RECOMMENDER.md).
Secondary layer: hard safety constraints (never invent actions, only block unsafe ones).
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.ai.decision.ml_recommender import (
    apply_safety_constraints,
    get_action_recommender,
)
from app.domain.entities.crowd import (
    ActionType,
    DecisionAction,
    DecisionBundle,
    RiskExplanation,
    RiskScore,
)


class CognitiveDecisionSupportEngine:
    """ML-based decision support with safety constraints."""

    def __init__(self):
        self.recommender = get_action_recommender()

    def _action_card(
        self,
        action_type: ActionType,
        *,
        zone_code: str,
        available_exits: list[str],
        adjacent_zones: list[str],
        score: float,
        priority: int,
        risk: RiskScore,
    ) -> DecisionAction:
        if action_type == ActionType.OPEN_EXIT:
            exit_name = available_exits[0]
            return DecisionAction(
                action_type=action_type,
                title=f"Open Exit Gate {exit_name}",
                payload={"exit": exit_name, "zone": zone_code},
                priority=priority,
                confidence=round(score, 3),
            )
        if action_type == ActionType.DEPLOY_GUARDS:
            guards = 5 if risk.dcrs >= 80 else 3
            return DecisionAction(
                action_type=action_type,
                title=f"Deploy {guards} Security Guards to {zone_code}",
                payload={"zone": zone_code, "guards": guards},
                priority=priority,
                confidence=round(score, 3),
            )
        if action_type == ActionType.REDIRECT_ZONE:
            target = adjacent_zones[0]
            return DecisionAction(
                action_type=action_type,
                title=f"Redirect Crowd to Zone {target}",
                payload={"from": zone_code, "to": target},
                priority=priority,
                confidence=round(score, 3),
            )
        if action_type == ActionType.ACTIVATE_PA:
            return DecisionAction(
                action_type=action_type,
                title="Activate Public Announcement — Slow Movement / Follow Marshals",
                payload={
                    "zone": zone_code,
                    "message": (
                        f"Attention in {zone_code}: please move calmly toward marked exits "
                        "and follow security instructions."
                    ),
                },
                priority=priority,
                confidence=round(score, 3),
            )
        if action_type == ActionType.ROUTE_EVACUATION:
            return DecisionAction(
                action_type=action_type,
                title="Prefer alternate evacuation corridor",
                payload={"zone": zone_code, "avoid_saturated_exits": True},
                priority=priority,
                confidence=round(score, 3),
            )
        if action_type == ActionType.DEPLOY_MEDICAL:
            return DecisionAction(
                action_type=action_type,
                title="Stage medical team near congestion edge",
                payload={"zone": zone_code, "teams": 1},
                priority=priority,
                confidence=round(score, 3),
            )
        if action_type == ActionType.HOLD_INGRESS:
            return DecisionAction(
                action_type=action_type,
                title="Temporarily hold ingress into high-risk zone",
                payload={"zone": zone_code, "minutes": 10},
                priority=priority,
                confidence=round(score, 3),
            )
        # CLOSE_EXIT kept for model completeness but usually filtered by safety
        return DecisionAction(
            action_type=action_type,
            title=f"Restrict secondary exit in {zone_code}",
            payload={"zone": zone_code},
            priority=priority,
            confidence=round(score, 3),
        )

    def recommend(
        self,
        *,
        alert_id: UUID | None,
        risk: RiskScore,
        explanation: RiskExplanation,
        zone_code: str,
        available_exits: list[str],
        adjacent_zones: list[str],
        feature_values: dict[str, float] | None = None,
    ) -> DecisionBundle:
        alert_id = alert_id or uuid4()

        # Build feature dict from explanation values when not provided
        features = feature_values or {
            c.feature: c.value for c in explanation.contributions
        }

        ranked = self.recommender.recommend(
            dcrs=risk.dcrs,
            band=risk.band.value,
            features=features,
            threshold=0.45,
            top_k=6,
        )
        ranked = apply_safety_constraints(
            ranked,
            available_exits=available_exits,
            adjacent_zones=adjacent_zones,
        )

        actions = [
            self._action_card(
                r.action_type,
                zone_code=zone_code,
                available_exits=available_exits,
                adjacent_zones=adjacent_zones,
                score=r.score,
                priority=r.priority,
                risk=risk,
            )
            for r in ranked
        ]

        top_feats = ", ".join(
            f"{n}={v:.2f}" for n, v in self.recommender.top_feature_importances(3)
        )
        confs = ", ".join(f"{a.action_type.value}:{a.confidence:.2f}" for a in actions[:3]) or "none"
        rationale = (
            f"Gradient Boosting recommender selected {len(actions)} actions for zone {zone_code} "
            f"(DCRS={risk.dcrs:.1f}, band={risk.band.value}). "
            f"Model confidences [{confs}]. "
            f"Top model features: {top_feats}. "
            f"Safety constraints filtered unsafe actions (e.g., closing last exit)."
        )
        return DecisionBundle(
            alert_id=alert_id,
            zone_id=risk.zone_id,
            dcrs=risk.dcrs,
            actions=actions,
            rationale=rationale,
        )
