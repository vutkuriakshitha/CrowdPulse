"""Lightweight multi-object tracker (centroid + IoU)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.ai.perception.detector import Detection


@dataclass
class Track:
    track_id: int
    bbox: list[float]
    confidence: float
    centroid: tuple[float, float]
    age: int = 1
    hits: int = 1
    time_since_update: int = 0


def _centroid(bbox: list[float]) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return inter / (area_a + area_b - inter + 1e-9)


def _foot_point(bbox: list[float]) -> tuple[float, float]:
    x1, _, x2, y2 = bbox
    return ((x1 + x2) / 2.0, y2)


class CentroidTracker:
    def __init__(self, max_lost: int = 15, iou_threshold: float = 0.2, dist_threshold: float = 80.0):
        self.max_lost = max_lost
        self.iou_threshold = iou_threshold
        self.dist_threshold = dist_threshold
        self._next_id = 1
        self.tracks: dict[int, Track] = {}

    def update(self, detections: list[Detection]) -> list[Track]:
        det_boxes = [d.bbox for d in detections]
        det_conf = [d.confidence for d in detections]
        track_ids = list(self.tracks.keys())

        if not track_ids:
            for box, conf in zip(det_boxes, det_conf):
                self._start_track(box, conf)
            return list(self.tracks.values())

        matched_t: set[int] = set()
        matched_d: set[int] = set()
        pairs: list[tuple[float, int, int]] = []

        for tid in track_ids:
            tb = self.tracks[tid].bbox
            tc = self.tracks[tid].centroid
            for di, db in enumerate(det_boxes):
                iou = _iou(tb, db)
                dc = _centroid(db)
                dist = float(np.hypot(tc[0] - dc[0], tc[1] - dc[1]))
                if iou >= self.iou_threshold or dist <= self.dist_threshold:
                    score = iou * 2.0 + max(0.0, 1.0 - dist / self.dist_threshold)
                    pairs.append((score, tid, di))
        pairs.sort(reverse=True)

        for _, tid, di in pairs:
            if tid in matched_t or di in matched_d:
                continue
            tr = self.tracks[tid]
            tr.bbox = det_boxes[di]
            tr.confidence = det_conf[di]
            tr.centroid = _centroid(tr.bbox)
            tr.hits += 1
            tr.age += 1
            tr.time_since_update = 0
            matched_t.add(tid)
            matched_d.add(di)

        for di, box in enumerate(det_boxes):
            if di not in matched_d:
                self._start_track(box, det_conf[di])
                matched_t.add(self._next_id - 1)

        for tid in list(self.tracks.keys()):
            if tid in matched_t:
                continue
            tr = self.tracks[tid]
            tr.time_since_update += 1
            tr.age += 1
            if tr.time_since_update > self.max_lost:
                del self.tracks[tid]

        return [t for t in self.tracks.values() if t.time_since_update == 0]

    def _start_track(self, box: list[float], conf: float) -> int:
        tid = self._next_id
        self._next_id += 1
        self.tracks[tid] = Track(tid, box, conf, _centroid(box))
        return tid

    @staticmethod
    def foot_points(tracks: list[Track]) -> list[tuple[int, tuple[float, float], float]]:
        return [(t.track_id, _foot_point(t.bbox), t.confidence) for t in tracks]
