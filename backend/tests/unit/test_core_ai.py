"""Unit tests for DCRS, fusion, and decision engine."""

from uuid import uuid4

import numpy as np

from app.ai.decision.cdse import CognitiveDecisionSupportEngine
from app.ai.fusion.multi_camera import Detection, HomographyProjector, MultiCameraFusion
from app.ai.risk.dcrs import DCRSEngine
from app.ai.xai.attributor import ExplainableRiskAttributor
from app.domain.entities.crowd import ActionType, RiskBand, ZoneMetrics


def test_dcrs_escalates_with_density_and_surge():
    engine = DCRSEngine()
    m = ZoneMetrics(
        zone_id=uuid4(),
        timestamp=0,
        count=1200,
        density=4.2,
        mean_speed=0.4,
        opposing_flow=0.7,
        group_cohesion=0.6,
        abnormal_motion=0.5,
        exit_pressure=1.2,
        forecast_surge=1.0,
        historical_hotspot=0.5,
        time_prior=0.7,
    )
    risk, _, _ = engine.evaluate(m)
    assert risk.dcrs >= 60
    assert risk.band in (RiskBand.ORANGE, RiskBand.RED)


def test_fusion_deduplicates_overlapping_cameras():
    H = np.eye(3)
    projector = HomographyProjector({"cam1": H, "cam2": H})
    fusion = MultiCameraFusion(projector, spatial_radius_m=1.0)
    dets = [
        Detection("cam1", 1, (100, 100, 140, 200), 0.9, 1.0, ground_xy=(5.0, 5.0)),
        Detection("cam2", 7, (110, 105, 150, 205), 0.88, 1.0, ground_xy=(5.2, 5.1)),
        Detection("cam1", 2, (400, 400, 440, 500), 0.91, 1.0, ground_xy=(20.0, 20.0)),
    ]
    fused = fusion.fuse(dets)
    assert len(fused) == 2


def test_cdse_emits_ml_ranked_recommendations():
    engine = DCRSEngine()
    xai = ExplainableRiskAttributor()
    cdse = CognitiveDecisionSupportEngine()
    m = ZoneMetrics(
        zone_id=uuid4(),
        timestamp=0,
        count=1000,
        density=3.8,
        mean_speed=0.5,
        opposing_flow=0.6,
        group_cohesion=0.5,
        abnormal_motion=0.4,
        exit_pressure=1.0,
        forecast_surge=0.8,
    )
    risk, feats, contribs = engine.evaluate(m)
    weights = {k: getattr(engine.weights, k) for k in feats}
    expl = xai.explain(
        risk_id=risk.id,
        zone_id=risk.zone_id,
        dcrs=risk.dcrs,
        features=feats,
        contributions=contribs,
        weights=weights,
    )
    bundle = cdse.recommend(
        alert_id=uuid4(),
        risk=risk,
        explanation=expl,
        zone_code="B",
        available_exits=["Gate-C"],
        adjacent_zones=["D"],
        feature_values=feats,
    )
    assert bundle.actions
    assert "Gradient Boosting" in bundle.rationale
    assert all(0.0 <= a.confidence <= 1.0 for a in bundle.actions)
    types = {a.action_type for a in bundle.actions}
    # High-risk dense zone should surface core operator actions
    assert types & {
        ActionType.OPEN_EXIT,
        ActionType.DEPLOY_GUARDS,
        ActionType.ACTIVATE_PA,
    }
    # Ranked by confidence descending
    confs = [a.confidence for a in bundle.actions]
    assert confs == sorted(confs, reverse=True)


def test_era_narrative_lists_top_risk_drivers():
    engine = DCRSEngine()
    xai = ExplainableRiskAttributor(top_k=5)
    m = ZoneMetrics(
        zone_id=uuid4(),
        timestamp=0,
        count=1200,
        density=4.0,
        mean_speed=0.3,
        opposing_flow=0.7,
        group_cohesion=0.5,
        abnormal_motion=0.4,
        exit_pressure=1.2,
        forecast_surge=1.0,
        historical_hotspot=0.5,
        time_prior=0.7,
    )
    risk, feats, contribs = engine.evaluate(m)
    weights = {k: getattr(engine.weights, k) for k in feats}
    expl = xai.explain(
        risk_id=risk.id,
        zone_id=risk.zone_id,
        dcrs=risk.dcrs,
        features=feats,
        contributions=contribs,
        weights=weights,
    )
    assert "Reason:" in expl.narrative
    assert "Risk Score" in expl.narrative
    # At least one of the core crowd drivers should appear in the why-text
    assert any(
        label in expl.narrative
        for label in (
            "Crowd density vs safe capacity",
            "Exit queue pressure",
            "Walking speed drop vs baseline",
            "Opposing / conflicting movement",
        )
    )
    top = ExplainableRiskAttributor.top_factors(expl, k=3)
    assert len(top) == 3
    assert "label" in top[0] and "contribution" in top[0]
