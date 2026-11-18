"""4-Point Planar Homography Ground Calibration for CrowdPulse.

Solves the camera perspective optical illusion:
- Distant pedestrians appear small (20px tall) and move few screen pixels per step.
- Foreground pedestrians appear huge (200px tall) and move many screen pixels per step.
- 4-point homography computes a 3x3 projective transformation matrix H that transforms
  camera screen pixels (u, v) into a top-down metric ground plane (X, Y) in meters.
- Yields true metric pedestrian speed (m/s) and true spatial density (p/m²).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import cv2
import numpy as np


@dataclass
class GroundCalibration:
    name: str
    src_pixel_quad: list[tuple[float, float]]  # 4 image points [TL, TR, BR, BL] in pixels
    dst_ground_quad_m: list[tuple[float, float]]  # 4 ground points [TL, TR, BR, BL] in meters
    homography_matrix: np.ndarray  # 3x3 projective matrix
    inverse_homography: np.ndarray  # 3x3 ground-to-image matrix


def compute_4point_homography(
    src_pixel_quad: Sequence[tuple[float, float]],
    dst_ground_quad_m: Sequence[tuple[float, float]],
    name: str = "default_camera",
) -> GroundCalibration:
    """Computes 3x3 Homography matrix H using cv2.getPerspectiveTransform."""
    if len(src_pixel_quad) != 4 or len(dst_ground_quad_m) != 4:
        raise ValueError("Exactly 4 corner points required for planar homography.")

    src = np.array(src_pixel_quad, dtype=np.float32)
    dst = np.array(dst_ground_quad_m, dtype=np.float32)

    H = cv2.getPerspectiveTransform(src, dst)
    H_inv = np.linalg.inv(H)

    return GroundCalibration(
        name=name,
        src_pixel_quad=list(src_pixel_quad),
        dst_ground_quad_m=list(dst_ground_quad_m),
        homography_matrix=H,
        inverse_homography=H_inv,
    )


class HomographyCalibrator:
    """Transforms raw camera coordinates to true metric venue coordinates."""

    def __init__(self, calibration: GroundCalibration):
        self.calib = calibration
        self.H = calibration.homography_matrix
        self.H_inv = calibration.inverse_homography

    @classmethod
    def from_tile_corners(
        cls,
        pixel_corners: Sequence[tuple[float, float]],
        tile_width_m: float,
        tile_length_m: float,
        name: str = "camera",
    ) -> HomographyCalibrator:
        """Convenience constructor: User clicks 4 corners of a known rectangle on the floor."""
        # Standard ordering: Top-Left, Top-Right, Bottom-Right, Bottom-Left
        ground_quad = [
            (0.0, 0.0),
            (tile_width_m, 0.0),
            (tile_width_m, tile_length_m),
            (0.0, tile_length_m),
        ]
        calib = compute_4point_homography(pixel_corners, ground_quad, name=name)
        return cls(calib)

    def image_to_ground(self, u: float, v: float) -> tuple[float, float]:
        """Convert screen pixel coordinate (u, v) -> ground plane coordinate (X, Y) in meters."""
        pt = np.array([u, v, 1.0], dtype=float)
        g = self.H @ pt
        scale = g[2] if abs(g[2]) > 1e-9 else 1e-9
        return float(g[0] / scale), float(g[1] / scale)

    def ground_to_image(self, x: float, y: float) -> tuple[float, float]:
        """Convert ground coordinate (X, Y) in meters -> screen pixel coordinate (u, v)."""
        pt = np.array([x, y, 1.0], dtype=float)
        p = self.H_inv @ pt
        scale = p[2] if abs(p[2]) > 1e-9 else 1e-9
        return float(p[0] / scale), float(p[1] / scale)

    def bbox_to_foot_ground(self, bbox: list[float] | tuple[float, float, float, float]) -> tuple[float, float]:
        """Foot point is bottom-center of bounding box."""
        x1, y1, x2, y2 = bbox
        foot_u = (x1 + x2) / 2.0
        foot_v = y2
        return self.image_to_ground(foot_u, foot_v)

    def compute_metric_speed(
        self,
        foot_pt_prev: tuple[float, float],
        foot_pt_curr: tuple[float, float],
        dt_seconds: float,
    ) -> float:
        """Compute true physical speed in meters/second (m/s)."""
        if dt_seconds <= 1e-4:
            return 0.0
        g_prev = self.image_to_ground(*foot_pt_prev)
        g_curr = self.image_to_ground(*foot_pt_curr)
        dist_meters = float(np.hypot(g_curr[0] - g_prev[0], g_curr[1] - g_prev[1]))
        return dist_meters / dt_seconds

    def compute_metric_density(
        self,
        pedestrian_boxes: list[list[float]],
        zone_ground_polygon_m: list[tuple[float, float]],
    ) -> tuple[int, float, float]:
        """Returns (count_in_zone, zone_area_m2, density_p_m2)."""
        from cv2 import pointPolygonTest

        poly_np = np.array(zone_ground_polygon_m, dtype=np.float32)
        # Compute area in m² using Shoelace formula / contourArea
        area_m2 = float(cv2.contourArea(poly_np))
        if area_m2 < 1.0:
            area_m2 = 1.0

        count = 0
        for b in pedestrian_boxes:
            gx, gy = self.bbox_to_foot_ground(b)
            if pointPolygonTest(poly_np, (float(gx), float(gy)), False) >= 0:
                count += 1

        density = count / area_m2
        return count, round(area_m2, 1), round(density, 2)


def get_default_concourse_calibrator(width: int = 640, height: int = 480) -> HomographyCalibrator:
    """Standard 4-point concourse CCTV ground calibration scaled to frame dimensions.
    
    Transforms camera perspective view into a top-down metric ground plane (meters).
    """
    sx = float(width) / 640.0
    sy = float(height) / 480.0
    src_pixel_quad = [
        (220.0 * sx, 140.0 * sy),  # Top-Left (Far ground)
        (420.0 * sx, 140.0 * sy),  # Top-Right (Far ground)
        (560.0 * sx, 440.0 * sy),  # Bottom-Right (Near ground)
        (80.0 * sx, 440.0 * sy),   # Bottom-Left (Near ground)
    ]
    return HomographyCalibrator.from_tile_corners(
        src_pixel_quad,
        tile_width_m=10.0,
        tile_length_m=10.0,
        name="standard_cctv_concourse",
    )

