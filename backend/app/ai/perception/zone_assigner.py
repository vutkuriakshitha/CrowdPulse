"""Assign tracked people to venue zones using image→venue mapping."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.ai.fusion.multi_camera import _point_in_poly


@dataclass
class ZoneDef:
    id: str
    code: str
    name: str
    polygon: list[tuple[float, float]]  # venue coordinates
    area_m2: float = 100.0


class ZoneAssigner:
    """Maps frame foot-points into venue zone polygons.

    Without per-camera homography calibration, we normalize image coordinates
    into the venue bounding box that covers all zone polygons. This is the
    Level-A operational mapper; calibrated HomographyProjector replaces it later.
    """

    def __init__(self, zones: list[ZoneDef], frame_width: int, frame_height: int):
        self.zones = zones
        self.frame_width = max(frame_width, 1)
        self.frame_height = max(frame_height, 1)
        xs = [p[0] for z in zones for p in z.polygon] or [0.0, 1.0]
        ys = [p[1] for z in zones for p in z.polygon] or [0.0, 1.0]
        self.min_x, self.max_x = min(xs), max(xs)
        self.min_y, self.max_y = min(ys), max(ys)
        if self.max_x <= self.min_x:
            self.max_x = self.min_x + 1.0
        if self.max_y <= self.min_y:
            self.max_y = self.min_y + 1.0

    def image_to_venue(self, x: float, y: float) -> tuple[float, float]:
        nx = x / self.frame_width
        ny = y / self.frame_height
        vx = self.min_x + nx * (self.max_x - self.min_x)
        vy = self.min_y + ny * (self.max_y - self.min_y)
        return vx, vy

    def assign(self, foot_xy: tuple[float, float]) -> ZoneDef | None:
        vx, vy = self.image_to_venue(foot_xy[0], foot_xy[1])
        for z in self.zones:
            if _point_in_poly(vx, vy, z.polygon):
                return z
        # nearest zone centroid fallback
        best = None
        best_d = 1e18
        for z in self.zones:
            cx = sum(p[0] for p in z.polygon) / max(len(z.polygon), 1)
            cy = sum(p[1] for p in z.polygon) / max(len(z.polygon), 1)
            d = (vx - cx) ** 2 + (vy - cy) ** 2
            if d < best_d:
                best_d = d
                best = z
        return best

    def count_by_zone(self, feet: list[tuple[float, float]]) -> dict[str, int]:
        counts = {z.code: 0 for z in self.zones}
        for ft in feet:
            z = self.assign(ft)
            if z:
                counts[z.code] = counts.get(z.code, 0) + 1
        return counts


def zones_from_venue_dict(venue_zones: list[dict]) -> list[ZoneDef]:
    out: list[ZoneDef] = []
    for z in venue_zones:
        poly = [(float(p[0]), float(p[1])) for p in (z.get("polygon") or [])]
        if len(poly) < 3:
            continue
        out.append(
            ZoneDef(
                id=str(z["id"]),
                code=z["code"],
                name=z.get("name", z["code"]),
                polygon=poly,
                area_m2=float(z.get("area_m2") or 100.0),
            )
        )
    return out
