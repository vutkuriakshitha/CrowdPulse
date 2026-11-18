from __future__ import annotations

import time
from uuid import UUID

from app.domain.entities.crowd import ZoneMetrics


class TwinStateStore:
    """Runtime twin cache for live metrics/alerts.

    Venue topology is loaded from DB via load_venue().
    Metrics/alerts remain in-process for Level A speed; persist later.
    """

    def __init__(self):
        self.venue: dict = {"id": "", "name": "", "zones": [], "cameras": []}
        self.metrics: dict[str, ZoneMetrics] = {}
        self.latest_risks: dict[str, dict] = {}
        self.alerts: list[dict] = []
        self.decisions: list[dict] = []

    def load_venue(self, venue: dict) -> None:
        self.venue = venue
        # Keep existing metrics if zone ids unchanged; otherwise reseed defaults
        existing = set(self.metrics.keys())
        incoming = {z["id"] for z in venue.get("zones", [])}
        if existing != incoming:
            self.metrics = {}
            self._seed_metrics()

    def _seed_metrics(self) -> None:
        now = time.time()
        seeds = {
            "A": (520, 2.1, 0.9, 0.2, 0.3, 0.4),
            "B": (1400, 3.5, 0.55, 0.55, 0.5, 0.9),
            "C": (410, 2.3, 0.7, 0.35, 0.4, 0.7),
            "D": (610, 2.0, 1.0, 0.15, 0.2, 0.3),
        }
        for z in self.venue.get("zones", []):
            count, dens, speed, opp, abn, exit_p = seeds.get(z["code"], (100, 1.0, 1.0, 0.1, 0.1, 0.2))
            self.metrics[z["id"]] = ZoneMetrics(
                zone_id=UUID(z["id"]),
                timestamp=now,
                count=count,
                density=dens,
                mean_speed=speed,
                opposing_flow=opp,
                group_cohesion=0.4,
                abnormal_motion=abn,
                exit_pressure=exit_p,
                weather_factor=0.0,
                time_prior=0.6,
                historical_hotspot=0.45 if z["code"] == "B" else 0.2,
                emergency_flag=0.0,
                forecast_surge=0.3 if z["code"] == "B" else 0.1,
            )

    def zone_meta_by_id(self) -> dict[str, dict]:
        return {z["id"]: z for z in self.venue.get("zones", [])}

    def adjacency(self) -> dict[str, list[str]]:
        code_to_id = {z["code"]: z["id"] for z in self.venue.get("zones", [])}
        return {
            z["id"]: [code_to_id[c] for c in z.get("adjacent", []) if c in code_to_id]
            for z in self.venue.get("zones", [])
        }


twin_store = TwinStateStore()
