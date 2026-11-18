"""Tests for Phase A: unmonitored no_data zone handling and cross-zone CDSE recommendations."""

from __future__ import annotations

import time
from uuid import uuid4

import pytest

from app.ai.decision.cdse import CognitiveDecisionSupportEngine
from app.ai.risk.dcrs import DCRSEngine
from app.ai.xai.attributor import ExplainableRiskAttributor
from app.application.use_cases.evaluate_risk import EvaluateVenueRiskUseCase
from app.domain.entities.crowd import ActionType, ZoneMetrics
from app.infrastructure.persistence.seed import DEMO_CAMERAS, DEMO_ZONES, VENUE_ID
from app.infrastructure.persistence.twin_store import twin_store


@pytest.fixture(autouse=True)
def setup_venue():
    demo_venue = {
        "id": str(VENUE_ID),
        "name": "Aether Arena",
        "zones": [
            {
                "id": str(z["id"]),
                "code": z["code"],
                "name": z["name"],
                "area_m2": z["area_m2"],
                "capacity": z["capacity"],
                "exits": z["exits"],
                "adjacent": z["adjacent"],
                "is_ingress": z["is_ingress"],
                "polygon": z["polygon"],
            }
            for z in DEMO_ZONES
        ],
        "cameras": DEMO_CAMERAS,
    }
    twin_store.reset_all_to_no_data()
    twin_store.load_venue(demo_venue)
    yield
    twin_store.reset_all_to_no_data()


def test_twin_store_zones_start_as_no_data():
    """Requirement 1: Zones start as 'no_data' (dcrs null, band 'unmonitored'), not zeros."""
    assert len(twin_store.metrics) == 0  # No fake zero metrics
    assert len(twin_store.latest_risks) == 4

    for zid, card in twin_store.latest_risks.items():
        assert card["status"] == "no_data"
        assert card["risk"]["dcrs"] is None
        assert card["risk"]["band"] == "unmonitored"
        assert card["metrics"] is None


def test_evaluate_risk_skips_no_data_zones():
    """Requirement 2: evaluate_risk skips no_data zones and evaluates only monitored zones."""
    res = EvaluateVenueRiskUseCase().execute()
    assert res["peak_dcrs"] is None
    assert res["peak_band"] == "unmonitored"
    assert len(res["alerts"]) == 0

    # All zones remain honest no_data
    for card in res["zones"]:
        assert card["status"] == "no_data"
        assert card["risk"]["dcrs"] is None
        assert card["risk"]["band"] == "unmonitored"


def test_cross_zone_recommendation_crowd_at_gate_b():
    """Requirement 3 & 4: Crowd at Gate B, with Zone D calmest, Zone A moderate, and Zone C no_data.

    - REDIRECT_ZONE must pick Zone D (lightest adjacent: DCRS ~24 vs Zone A ~40).
    - Zone C (no_data) must NEVER be chosen.
    - OPEN_EXIT must pick Gate-D (served by Zone D with lowest DCRS).
    - Titles and payloads must display explicit comparative reasons.
    """
    code_to_id = {z["code"]: str(z["id"]) for z in DEMO_ZONES}
    now = time.time()

    # Zone B is heavily congested
    twin_store.set_zone_metrics(
        code_to_id["B"],
        ZoneMetrics(
            zone_id=uuid4(),
            timestamp=now,
            count=1200,
            density=3.5,
            mean_speed=0.3,
            opposing_flow=0.6,
            group_cohesion=0.5,
            abnormal_motion=0.4,
            exit_pressure=1.2,
            forecast_surge=0.8,
            time_prior=0.5,
        ),
    )

    # Zone A has moderate pedestrian flow
    twin_store.set_zone_metrics(
        code_to_id["A"],
        ZoneMetrics(
            zone_id=uuid4(),
            timestamp=now,
            count=200,
            density=1.0,
            mean_speed=0.8,
            opposing_flow=0.3,
            group_cohesion=0.2,
            abnormal_motion=0.0,
            exit_pressure=0.3,
            forecast_surge=0.1,
            time_prior=0.3,
        ),
    )

    # Zone D is the calmest monitored zone
    twin_store.set_zone_metrics(
        code_to_id["D"],
        ZoneMetrics(
            zone_id=uuid4(),
            timestamp=now,
            count=15,
            density=0.1,
            mean_speed=1.2,
            opposing_flow=0.0,
            group_cohesion=0.0,
            abnormal_motion=0.0,
            exit_pressure=0.0,
            forecast_surge=0.0,
            time_prior=0.0,
        ),
    )

    # Note: Zone C is left unmonitored (no metrics set -> no_data)

    res = EvaluateVenueRiskUseCase().execute()
    assert len(res["alerts"]) >= 1

    alert_b = next((a for a in res["alerts"] if a["zone_code"] == "B"), None)
    assert alert_b is not None
    assert alert_b["dcrs"] >= 60.0  # Orange/Red alert threshold

    actions = alert_b["actions"]
    redirect = next((a for a in actions if a["action_type"] == ActionType.REDIRECT_ZONE.value), None)
    open_exit = next((a for a in actions if a["action_type"] == ActionType.OPEN_EXIT.value), None)

    assert redirect is not None
    # REDIRECT_ZONE picks Zone D because it is lighter than Zone A (and Zone C has no data)
    assert redirect["payload"]["to"] == "D"
    assert redirect["payload"]["to"] != "C"  # NEVER choose no_data zone
    assert "Redirect Crowd to Zone D" in redirect["title"]
    assert "vs Zone B" in redirect["title"]
    assert redirect["payload"]["target_dcrs"] < redirect["payload"]["source_dcrs"]

    assert open_exit is not None
    # OPEN_EXIT picks Gate-D served by adjacent Zone D (lowest DCRS among adjacent zones with data)
    assert open_exit["payload"]["serving_zone"] == "D"
    assert "Gate-D" in open_exit["payload"]["exit"]
    assert "Open Gate-D" in open_exit["title"]
    assert "Gate Gate" not in open_exit["title"]
    assert "vs Zone B" in open_exit["title"]


def test_cross_zone_recommendation_crowd_at_gate_d_switches_sensibly():
    """Requirement 4: When crowd shifts to Gate D, recommendation switches to Gate-B / Zone B."""
    code_to_id = {z["code"]: str(z["id"]) for z in DEMO_ZONES}
    now = time.time()

    # Zone D is heavily congested
    twin_store.set_zone_metrics(
        code_to_id["D"],
        ZoneMetrics(
            zone_id=uuid4(),
            timestamp=now,
            count=1100,
            density=3.6,
            mean_speed=0.25,
            opposing_flow=0.7,
            group_cohesion=0.5,
            abnormal_motion=0.4,
            exit_pressure=1.3,
            forecast_surge=0.9,
            time_prior=0.5,
        ),
    )

    # Zone B is now calmest
    twin_store.set_zone_metrics(
        code_to_id["B"],
        ZoneMetrics(
            zone_id=uuid4(),
            timestamp=now,
            count=15,
            density=0.1,
            mean_speed=1.2,
            opposing_flow=0.0,
            group_cohesion=0.0,
            abnormal_motion=0.0,
            exit_pressure=0.0,
            forecast_surge=0.0,
            time_prior=0.0,
        ),
    )

    # Zone A is moderately loaded
    twin_store.set_zone_metrics(
        code_to_id["A"],
        ZoneMetrics(
            zone_id=uuid4(),
            timestamp=now,
            count=200,
            density=1.0,
            mean_speed=0.8,
            opposing_flow=0.3,
            group_cohesion=0.2,
            abnormal_motion=0.0,
            exit_pressure=0.3,
            forecast_surge=0.1,
            time_prior=0.3,
        ),
    )

    # Zone C remains no_data

    res = EvaluateVenueRiskUseCase().execute()
    alert_d = next((a for a in res["alerts"] if a["zone_code"] == "D"), None)
    assert alert_d is not None
    assert alert_d["dcrs"] >= 60.0

    actions = alert_d["actions"]
    redirect = next((a for a in actions if a["action_type"] == ActionType.REDIRECT_ZONE.value), None)
    open_exit = next((a for a in actions if a["action_type"] == ActionType.OPEN_EXIT.value), None)

    assert redirect is not None
    # Zone D is adjacent to B and C. Zone C is no_data, so Zone B is chosen!
    assert redirect["payload"]["to"] == "B"
    assert redirect["payload"]["to"] != "C"
    assert "Redirect Crowd to Zone B" in redirect["title"]
    assert "vs Zone D" in redirect["title"]

    assert open_exit is not None
    # Alternate zones with data are A and B. Zone B has the lowest DCRS, so its exit Gate-B is picked!
    assert open_exit["payload"]["serving_zone"] == "B"
    assert "Gate-B" in open_exit["payload"]["exit"]
    assert "Open Gate-B" in open_exit["title"]
    assert "Gate Gate" not in open_exit["title"]
    assert "vs Zone D" in open_exit["title"]


def test_no_adjacent_data_reported_honestly():
    """When a crowded zone has no adjacent monitored zones with data, report clearly."""
    cdse = CognitiveDecisionSupportEngine()
    engine = DCRSEngine()
    xai = ExplainableRiskAttributor()

    m = ZoneMetrics(
        zone_id=uuid4(),
        timestamp=0,
        count=1000,
        density=3.8,
        mean_speed=0.4,
        opposing_flow=0.5,
        group_cohesion=0.5,
        abnormal_motion=0.4,
        exit_pressure=1.0,
        forecast_surge=0.8,
    )
    risk, feats, contribs = engine.evaluate(m)
    expl = xai.explain(
        risk_id=risk.id,
        zone_id=risk.zone_id,
        dcrs=risk.dcrs,
        features=feats,
        contributions=contribs,
        weights={k: getattr(engine.weights, k) for k in feats},
    )

    # Only Zone B has data; adjacent zones C and D have no data
    bundle = cdse.recommend(
        alert_id=uuid4(),
        risk=risk,
        explanation=expl,
        zone_code="B",
        available_exits=["Gate-B"],
        adjacent_zones=["C", "D"],
        feature_values=feats,
        all_zone_risks={"B": risk.dcrs},  # only B has data
        all_zone_exits={"B": ["Gate-B"], "C": ["Gate-C"], "D": ["Gate-D"]},
    )

    redirect = next((a for a in bundle.actions if a.action_type == ActionType.REDIRECT_ZONE), None)
    assert redirect is not None
    assert redirect.payload["to"] is None
    assert "no adjacent monitored zones with active data" in redirect.title
    assert "cannot safely redirect" in redirect.payload["reason"]

    open_exit = next((a for a in bundle.actions if a.action_type == ActionType.OPEN_EXIT), None)
    assert open_exit is not None
    assert open_exit.payload["exit"] is None
    assert "No adjacent exit with data" in open_exit.title
    assert "No adjacent exit with data" in open_exit.payload["reason"]

