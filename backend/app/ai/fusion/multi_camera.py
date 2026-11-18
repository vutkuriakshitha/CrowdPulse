"""Multi-camera fusion with anti-double-counting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

import numpy as np


@dataclass
class Detection:
    camera_id: str
    track_id: int
    bbox: tuple[float, float, float, float]  # x1,y1,x2,y2 in image coords
    confidence: float
    timestamp: float
    embedding: np.ndarray | None = None
    ground_xy: tuple[float, float] | None = None  # meters in venue frame


@dataclass
class FusedPerson:
    global_id: str
    ground_xy: tuple[float, float]
    cameras: list[str]
    confidence: float
    timestamp: float


class HomographyProjector:
    """Projects image points to venue ground plane using a 3x3 homography."""

    def __init__(self, homographies: dict[str, np.ndarray]):
        self.homographies = {k: np.asarray(v, dtype=float) for k, v in homographies.items()}

    def project(self, camera_id: str, bbox: tuple[float, float, float, float]) -> tuple[float, float]:
        H = self.homographies[camera_id]
        x1, y1, x2, y2 = bbox
        # foot point approx
        u, v = (x1 + x2) / 2.0, y2
        p = np.array([u, v, 1.0])
        g = H @ p
        g /= g[2] + 1e-9
        return float(g[0]), float(g[1])


class MultiCameraFusion:
    """Fuses overlapping camera detections to prevent double counting.

    Strategy:
    1. Project detections to shared ground plane
    2. Spatially cluster within radius
    3. Optionally refine with embedding cosine similarity
    """

    def __init__(
        self,
        projector: HomographyProjector,
        spatial_radius_m: float = 0.7,
        embedding_threshold: float = 0.55,
    ):
        self.projector = projector
        self.spatial_radius_m = spatial_radius_m
        self.embedding_threshold = embedding_threshold

    def fuse(self, detections: Iterable[Detection]) -> list[FusedPerson]:
        prepared: list[Detection] = []
        for d in detections:
            if d.ground_xy is None:
                d.ground_xy = self.projector.project(d.camera_id, d.bbox)
            prepared.append(d)

        clusters: list[list[Detection]] = []
        for det in prepared:
            matched = False
            for cluster in clusters:
                if self._belongs(det, cluster):
                    cluster.append(det)
                    matched = True
                    break
            if not matched:
                clusters.append([det])

        fused: list[FusedPerson] = []
        for idx, cluster in enumerate(clusters):
            xs = [c.ground_xy[0] for c in cluster if c.ground_xy]
            ys = [c.ground_xy[1] for c in cluster if c.ground_xy]
            fused.append(
                FusedPerson(
                    global_id=f"g-{int(cluster[0].timestamp)}-{idx}",
                    ground_xy=(float(np.mean(xs)), float(np.mean(ys))),
                    cameras=sorted({c.camera_id for c in cluster}),
                    confidence=float(np.mean([c.confidence for c in cluster])),
                    timestamp=max(c.timestamp for c in cluster),
                )
            )
        return fused

    def _belongs(self, det: Detection, cluster: list[Detection]) -> bool:
        assert det.ground_xy is not None
        for other in cluster:
            assert other.ground_xy is not None
            dist = np.linalg.norm(np.array(det.ground_xy) - np.array(other.ground_xy))
            if dist > self.spatial_radius_m:
                continue
            if det.embedding is not None and other.embedding is not None:
                sim = self._cosine(det.embedding, other.embedding)
                if sim < self.embedding_threshold:
                    continue
            # same camera + different track unlikely same person at same time
            if det.camera_id == other.camera_id and det.track_id != other.track_id:
                continue
            return True
        return False

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        na = np.linalg.norm(a) + 1e-9
        nb = np.linalg.norm(b) + 1e-9
        return float(np.dot(a, b) / (na * nb))


def assign_zone(point: tuple[float, float], zone_polygons: dict[UUID, list[tuple[float, float]]]) -> UUID | None:
    """Ray-casting point-in-polygon zone assignment."""
    x, y = point
    for zone_id, poly in zone_polygons.items():
        if _point_in_poly(x, y, poly):
            return zone_id
    return None


def _point_in_poly(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1):
            inside = not inside
    return inside
