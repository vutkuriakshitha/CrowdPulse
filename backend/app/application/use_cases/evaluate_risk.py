"""Application use-case: evaluate live risk + decisions for all zones."""

from __future__ import annotations

import time
from uuid import UUID, uuid4

from app.ai.decision.cdse import CognitiveDecisionSupportEngine
from app.ai.forecasting.zone_forecaster import ZoneGraphForecaster, ZoneNodeState
from app.ai.risk.dcrs import DCRSEngine
from app.ai.xai.attributor import ExplainableRiskAttributor
from app.core.config import settings
from app.infrastructure.persistence.twin_store import twin_store


class EvaluateVenueRiskUseCase:
    def __init__(self):
        self.risk = DCRSEngine()
        self.xai = ExplainableRiskAttributor()
        self.cdse = CognitiveDecisionSupportEngine()
        self.forecaster = ZoneGraphForecaster(twin_store.adjacency())

    def _actions_payload(self, bundle) -> list[dict]:
        actions = []
        for a in bundle.actions:
            d = a.model_dump(mode="json")
            d.setdefault("status", "pending")
            actions.append(d)
        return actions

    def _sync_decision(self, alert: dict) -> None:
        aid = str(alert["id"])
        for d in twin_store.decisions:
            if d.get("alert_id") == aid:
                d["actions"] = alert.get("actions") or []
                d["rationale"] = alert.get("rationale") or ""
                d["zone_code"] = alert.get("zone_code")
                return
        twin_store.decisions.insert(
            0,
            {
                "alert_id": aid,
                "zone_code": alert.get("zone_code"),
                "actions": alert.get("actions") or [],
                "rationale": alert.get("rationale") or "",
            },
        )

    def execute(self, *, clear_alerts: bool = False) -> dict:
        self.forecaster = ZoneGraphForecaster(twin_store.adjacency())
        meta = twin_store.zone_meta_by_id()
        if not meta:
            return {
                "venue": twin_store.venue,
                "zones": [],
                "alerts": [],
                "generated_at": time.time(),
                "error": "No zones loaded from database",
            }
        if clear_alerts:
            twin_store.alerts = []
            twin_store.decisions = []

        # Keep open alerts stable across twin polls so Accept/Dismiss survives refresh
        open_by_zone = {
            a["zone_code"]: a
            for a in twin_store.alerts
            if a.get("queue_status", "open") == "open" and a.get("zone_code")
        }

        states = {}
        for zid, m in twin_store.metrics.items():
            states[zid] = ZoneNodeState(
                zone_id=zid,
                density=m.density,
                mean_speed=m.mean_speed,
                outflow=max(0.05, m.mean_speed * (1 - min(m.exit_pressure, 1))),
                inflow=0.15 + 0.1 * m.time_prior,
            )
        forecasts = self.forecaster.forecast(states, settings.forecast_horizons_min)

        zone_cards = []
        for zid, m in twin_store.metrics.items():
            m.timestamp = time.time()
            fut10 = forecasts[zid].get(10, m.density)
            forecast_surge = self.forecaster.surge_feature(m.density, fut10)
            if m.forecast_surge < forecast_surge:
                m.forecast_surge = forecast_surge
            risk, feats, contribs = self.risk.evaluate(m, horizon_minutes=10, forecast_dcrs=None)
            weights = {k: getattr(self.risk.weights, k) for k in feats}
            expl = self.xai.explain(
                risk_id=risk.id,
                zone_id=risk.zone_id,
                dcrs=risk.dcrs,
                features=feats,
                contributions=contribs,
                weights=weights,
            )
            z = meta[zid]
            twin_store.latest_risks[zid] = {
                "zone": z,
                "metrics": m.model_dump(mode="json"),
                "risk": risk.model_dump(mode="json"),
                "explanation": expl.model_dump(mode="json"),
                "features": feats,
                "forecast_density": forecasts[zid],
            }
            zone_cards.append(twin_store.latest_risks[zid])

            should_alert = risk.dcrs >= settings.risk_orange_threshold
            factors = ExplainableRiskAttributor.top_factors(expl, k=5)
            explanation_payload = {
                "narrative": expl.narrative,
                "contributions": factors,
                "top_labels": [f["label"] for f in factors[:3]],
            }

            if not should_alert:
                continue

            existing = open_by_zone.get(z["code"])
            if existing:
                existing["dcrs"] = risk.dcrs
                existing["band"] = risk.band.value
                existing["severity"] = "critical" if risk.band.value == "red" else "warning"
                existing["explanation"] = explanation_payload
                acted = any(
                    (a.get("status") or "pending") in ("accepted", "dismissed")
                    for a in existing.get("actions") or []
                )
                if not acted:
                    aid = UUID(str(existing["id"]))
                    bundle = self.cdse.recommend(
                        alert_id=aid,
                        risk=risk,
                        explanation=expl,
                        zone_code=z["code"],
                        available_exits=z.get("exits", []),
                        adjacent_zones=z.get("adjacent", []),
                        feature_values=feats,
                    )
                    existing["actions"] = self._actions_payload(bundle)
                    existing["rationale"] = bundle.rationale
                    self._sync_decision(existing)
                continue

            alert_id = uuid4()
            bundle = self.cdse.recommend(
                alert_id=alert_id,
                risk=risk,
                explanation=expl,
                zone_code=z["code"],
                available_exits=z.get("exits", []),
                adjacent_zones=z.get("adjacent", []),
                feature_values=feats,
            )
            actions = self._actions_payload(bundle)
            alert = {
                "id": str(alert_id),
                "zone_id": zid,
                "zone_code": z["code"],
                "dcrs": risk.dcrs,
                "band": risk.band.value,
                "severity": "critical" if risk.band.value == "red" else "warning",
                "explanation": explanation_payload,
                "actions": actions,
                "rationale": bundle.rationale,
                "queue_status": "open",
                "created_at": time.time(),
            }
            twin_store.alerts.insert(0, alert)
            open_by_zone[z["code"]] = alert
            twin_store.decisions.insert(
                0,
                {
                    "alert_id": str(alert_id),
                    "zone_code": z["code"],
                    "actions": actions,
                    "rationale": bundle.rationale,
                },
            )

        twin_store.alerts = twin_store.alerts[:50]
        twin_store.decisions = twin_store.decisions[:50]
        zone_cards.sort(key=lambda c: c["risk"]["dcrs"], reverse=True)
        open_alerts = [a for a in twin_store.alerts if a.get("queue_status", "open") == "open"]
        return {
            "venue": twin_store.venue,
            "zones": zone_cards,
            "alerts": open_alerts[:20],
            "generated_at": time.time(),
            "peak_dcrs": zone_cards[0]["risk"]["dcrs"] if zone_cards else 0.0,
            "peak_zone": zone_cards[0]["zone"]["code"] if zone_cards else None,
            "peak_band": zone_cards[0]["risk"]["band"] if zone_cards else None,
        }
