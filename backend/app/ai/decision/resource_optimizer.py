"""Resource optimization for evacuation and asset placement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import networkx as nx


@dataclass
class Resource:
    id: str
    type: str  # guard | medical | vehicle
    capacity: int
    location_zone: str


class ResourceOptimizer:
    """Graph-based evacuation routing and greedy asset deployment."""

    def __init__(self, graph: nx.DiGraph):
        """graph edges should include attribute `travel_cost` and `congestion`."""
        self.graph = graph

    def best_evacuation_path(self, source: str, exits: List[str]) -> Tuple[List[str], float]:
        best_path: List[str] = []
        best_cost = float("inf")
        for exit_node in exits:
            try:
                path = nx.shortest_path(
                    self.graph,
                    source,
                    exit_node,
                    weight=self._edge_weight,
                )
                cost = nx.path_weight(self.graph, path, weight=self._edge_weight)
                if cost < best_cost:
                    best_cost = cost
                    best_path = path
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
        return best_path, best_cost if best_path else float("inf")

    def deploy_resources(
        self,
        resources: List[Resource],
        risk_by_zone: Dict[str, float],
        top_k: int = 5,
    ) -> Dict[str, List[str]]:
        """Greedy assign highest-capacity free resources to riskiest zones."""
        zones = sorted(risk_by_zone.items(), key=lambda x: x[1], reverse=True)[:top_k]
        assignments: Dict[str, List[str]] = {z: [] for z, _ in zones}
        pool = sorted(resources, key=lambda r: r.capacity, reverse=True)
        zi = 0
        for res in pool:
            if not zones:
                break
            zone, _ = zones[zi % len(zones)]
            assignments[zone].append(res.id)
            zi += 1
        return assignments

    @staticmethod
    def _edge_weight(u, v, attrs) -> float:  # noqa: ARG001
        return float(attrs.get("travel_cost", 1.0)) * (1.0 + float(attrs.get("congestion", 0.0)))
