"""What-if simulation engine on live twin state (Day 15)."""

from __future__ import annotations

import time
from copy import deepcopy
from uuid import uuid4

from app.ai.decision.cdse import CognitiveDecisionSupportEngine
from app.ai.forecasting.zone_forecaster import ZoneGraphForecaster, ZoneNodeState
from app.ai.risk.dcrs import DCRSEngine
from app.ai.xai.attributor import ExplainableRiskAttributor
from app.domain.entities.crowd import (
    SimulationResult,
    SimulationScenario,
    ZoneMetrics,
)


class WhatIfSimulator:
    """Perturbs twin state and re-forecasts congestion / risk.

    Closing an exit only stresses zones that use that exit (plus light adjacent spillover),
    so predicted peak DCRS rises relative to the live baseline.
    """

    def __init__(
        self,
        forecaster: ZoneGraphForecaster,
        risk_engine: DCRSEngine | None = None,
        cdse: CognitiveDecisionSupportEngine | None = None,
    ):
        self.forecaster = forecaster
        self.risk_engine = risk_engine or DCRSEngine()
        self.cdse = cdse or CognitiveDecisionSupportEngine()
        self.xai = ExplainableRiskAttributor()

    def _peak_from_metrics(
        self,
        metrics: dict[str, ZoneMetrics],
        zone_meta: dict[str, dict],
        *,
        horizon_minutes: int,
    ) -> float:
        states = {
            zid: ZoneNodeState(
                zone_id=zid,
                density=m.density,
                mean_speed=m.mean_speed,
                outflow=max(0.1, m.mean_speed * (1.0 - min(m.exit_pressure, 1.0))),
                inflow=0.2 + 0.1 * m.time_prior,
            )
            for zid, m in metrics.items()
        }
        forecasts = self.forecaster.forecast(states, [horizon_minutes])
        peak = 0.0
        for zid, m in metrics.items():
            fut = forecasts[zid][horizon_minutes]
            tmp = deepcopy(m)
            tmp.forecast_surge = self.forecaster.surge_feature(tmp.density, fut)
            risk, _, _ = self.risk_engine.evaluate(tmp, horizon_minutes=horizon_minutes)
            peak = max(peak, risk.dcrs)
        return peak

    def _apply_scenario(
        self,
        scenario: SimulationScenario,
        base_metrics: dict[str, ZoneMetrics],
        zone_meta: dict[str, dict],
    ) -> dict[str, ZoneMetrics]:
        metrics = {k: deepcopy(v) for k, v in base_metrics.items()}
        closed = {e.strip() for e in (scenario.close_exits or []) if e and str(e).strip()}
        code_to_id = {meta.get("code"): zid for zid, meta in zone_meta.items()}

        affected_zone_ids: set[str] = set()
        for zid, meta in zone_meta.items():
            zone_exits = set(meta.get("exits") or [])
            if closed & zone_exits:
                affected_zone_ids.add(zid)

        # Adjacent spillover when a neighbor loses exit capacity
        spillover_ids: set[str] = set()
        for zid in affected_zone_ids:
            for adj_code in zone_meta[zid].get("adjacent") or []:
                adj_id = code_to_id.get(adj_code)
                if adj_id and adj_id not in affected_zone_ids:
                    spillover_ids.add(adj_id)

        for zid, m in metrics.items():
            meta = zone_meta[zid]
            zone_exits = list(meta.get("exits") or [])
            lost = [e for e in zone_exits if e in closed]
            remaining = [e for e in zone_exits if e not in closed]
            meta["exits_effective"] = remaining

            if scenario.rainfall_mm_h > 0:
                m.weather_factor = min(1.0, scenario.rainfall_mm_h / 20.0)
                m.mean_speed *= max(0.45, 1.0 - 0.035 * scenario.rainfall_mm_h)
                m.opposing_flow = min(1.0, m.opposing_flow + 0.05 * (scenario.rainfall_mm_h / 20.0))

            if scenario.vip_zone and meta.get("code") == scenario.vip_zone.upper():
                m.density *= 1.28
                m.group_cohesion = min(1.0, m.group_cohesion + 0.22)
                m.forecast_surge = min(2.0, m.forecast_surge + 0.25)

            if lost:
                # Stronger pressure when a zone loses exits it actually uses
                lost_ratio = len(lost) / max(len(zone_exits), 1)
                m.exit_pressure = min(2.0, m.exit_pressure + 0.9 + 0.9 * lost_ratio)
                m.mean_speed *= max(0.4, 1.0 - 0.25 * lost_ratio)
                m.density *= 1.0 + 0.12 * lost_ratio
                m.forecast_surge = min(2.0, m.forecast_surge + 0.35 + 0.4 * lost_ratio)
                if not remaining:
                    # Last exit closed — emergency-level pressure
                    m.exit_pressure = 2.0
                    m.emergency_flag = 1.0
                    m.forecast_surge = min(2.0, m.forecast_surge + 0.5)
            elif zid in spillover_ids:
                m.exit_pressure = min(2.0, m.exit_pressure + 0.35)
                m.forecast_surge = min(2.0, m.forecast_surge + 0.15)
                m.density *= 1.06

            if scenario.hold_ingress and meta.get("is_ingress"):
                m.forecast_surge = max(0.0, m.forecast_surge - 0.4)
                m.density *= 0.9

        return metrics

    def run(
        self,
        *,
        scenario: SimulationScenario,
        base_metrics: dict[str, ZoneMetrics],
        zone_meta: dict[str, dict],
    ) -> SimulationResult:
        if not base_metrics or not zone_meta:
            return SimulationResult(
                scenario=scenario,
                predicted_peak_dcrs=0.0,
                baseline_peak_dcrs=0.0,
                dcrs_delta=0.0,
                congested_zones=[],
                recommended_actions=[],
                narrative="No twin metrics available for simulation.",
                zone_risks=[],
            )

        # Normalize VIP zone code
        if scenario.vip_zone:
            scenario = scenario.model_copy(update={"vip_zone": scenario.vip_zone.strip().upper() or None})

        # Deep-copy zone meta so exits_effective does not mutate live twin topology
        zone_meta = {zid: deepcopy(meta) for zid, meta in zone_meta.items()}

        baseline_peak = self._peak_from_metrics(
            {k: deepcopy(v) for k, v in base_metrics.items()},
            zone_meta,
            horizon_minutes=scenario.horizon_minutes,
        )

        metrics = self._apply_scenario(scenario, base_metrics, zone_meta)

        states = {
            zid: ZoneNodeState(
                zone_id=zid,
                density=m.density,
                mean_speed=m.mean_speed,
                outflow=max(0.1, m.mean_speed * (1.0 - min(m.exit_pressure, 1.0))),
                inflow=0.2 + 0.1 * m.time_prior,
            )
            for zid, m in metrics.items()
        }
        forecasts = self.forecaster.forecast(states, [scenario.horizon_minutes])

        peak = 0.0
        congested: list[str] = []
        best_actions = []
        zone_risks: list[dict] = []

        for zid, m in metrics.items():
            fut = forecasts[zid][scenario.horizon_minutes]
            m.forecast_surge = self.forecaster.surge_feature(m.density, fut)
            risk, feats, contribs = self.risk_engine.evaluate(
                m, horizon_minutes=scenario.horizon_minutes
            )
            code = zone_meta[zid]["code"]
            peak = max(peak, risk.dcrs)
            zone_risks.append(
                {
                    "zone_code": code,
                    "dcrs": round(risk.dcrs, 2),
                    "band": risk.band.value,
                    "density": round(m.density, 3),
                    "exit_pressure": round(m.exit_pressure, 3),
                    "forecast_density": round(float(fut), 3),
                    "exits_effective": zone_meta[zid].get("exits_effective", zone_meta[zid].get("exits", [])),
                }
            )
            if risk.dcrs >= 60:
                congested.append(code)
                weights = {k: getattr(self.risk_engine.weights, k) for k in feats}
                expl = self.xai.explain(
                    risk_id=risk.id,
                    zone_id=m.zone_id,
                    dcrs=risk.dcrs,
                    features=feats,
                    contributions=contribs,
                    weights=weights,
                )
                bundle = self.cdse.recommend(
                    alert_id=uuid4(),
                    risk=risk,
                    explanation=expl,
                    zone_code=code,
                    available_exits=zone_meta[zid].get(
                        "exits_effective", zone_meta[zid].get("exits", [])
                    ),
                    adjacent_zones=zone_meta[zid].get("adjacent", []),
                    feature_values=feats,
                )
                best_actions.extend(bundle.actions)

        zone_risks.sort(key=lambda r: r["dcrs"], reverse=True)
        delta = round(peak - baseline_peak, 2)

        parts = [
            f"Scenario '{scenario.name}' over {scenario.horizon_minutes} min → "
            f"peak DCRS {peak:.1f} (baseline {baseline_peak:.1f}, Δ {delta:+.1f})."
        ]
        if scenario.close_exits:
            parts.append(f"Closed exits: {', '.join(scenario.close_exits)}.")
        if scenario.rainfall_mm_h > 0:
            parts.append(f"Rainfall {scenario.rainfall_mm_h:.0f} mm/h.")
        if scenario.vip_zone:
            parts.append(f"VIP ingress in zone {scenario.vip_zone}.")
        parts.append(f"Congested zones: {', '.join(sorted(set(congested))) or 'none'}.")
        if delta > 0.5:
            parts.append("Predicted risk increases versus current twin — pre-stage mitigations.")
        elif delta < -0.5:
            parts.append("Predicted risk decreases versus current twin.")

        uniq = []
        seen = set()
        for a in best_actions:
            key = (a.action_type, a.title)
            if key not in seen:
                seen.add(key)
                uniq.append(a)

        return SimulationResult(
            scenario=scenario,
            predicted_peak_dcrs=round(peak, 2),
            baseline_peak_dcrs=round(baseline_peak, 2),
            dcrs_delta=delta,
            congested_zones=sorted(set(congested)),
            recommended_actions=uniq[:8],
            narrative=" ".join(parts),
            zone_risks=zone_risks,
            generated_at=time.time(),
        )
