"""Person detection engines for CCTV frames.

Primary: Ultralytics YOLO nano (yolov8n) — small/fast for demos
Fallback: OpenCV HOG pedestrian detector (CPU-friendly)
Both engines are cached in-process via lru_cache.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    bbox: list[float]  # x1,y1,x2,y2
    confidence: float
    class_name: str = "person"


@dataclass
class EngineInfo:
    name: str
    backend: str


class PersonDetector:
    def detect(self, frame: np.ndarray) -> list[Detection]:
        raise NotImplementedError

    @property
    def info(self) -> EngineInfo:
        raise NotImplementedError


class YoloPersonDetector(PersonDetector):
    def __init__(
        self,
        model_name: str | None = None,
        conf: float | None = None,
        imgsz: int | None = None,
        iou: float | None = None,
    ):
        from ultralytics import YOLO  # type: ignore

        self._name = model_name or settings.yolo_model_name
        self.conf = conf if conf is not None else settings.yolo_conf
        self.imgsz = imgsz if imgsz is not None else settings.yolo_imgsz
        self.iou = iou if iou is not None else settings.yolo_iou
        self.model = YOLO(self._name)

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(name=self._name, backend="ultralytics-yolo")

    def detect(self, frame: np.ndarray) -> list[Detection]:
        results = self.model.predict(
            frame,
            conf=self.conf,
            iou=self.iou,
            classes=[0],  # person only
            imgsz=self.imgsz,
            max_det=200,
            verbose=False,
        )
        out: list[Detection] = []
        if not results:
            return out
        boxes = results[0].boxes
        if boxes is None:
            return out
        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i].tolist()
            conf = float(boxes.conf[i])
            out.append(Detection(bbox=xyxy, confidence=conf))
        return out


class HogPersonDetector(PersonDetector):
    """OpenCV HOG + SVM pedestrian detector (CPU-friendly fallback)."""

    def __init__(self):
        import cv2

        self.cv2 = cv2
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(name="hog-pedestrian", backend="opencv")

    def detect(self, frame: np.ndarray) -> list[Detection]:
        # Downscale large frames for demo speed; HOG is expensive on full HD
        h, w = frame.shape[:2]
        scale = 1.0
        img = frame
        target = 480
        if max(h, w) > target:
            scale = target / max(h, w)
            img = self.cv2.resize(frame, (int(w * scale), int(h * scale)))
        elif max(h, w) < 360:
            scale = 360 / max(h, w)
            img = self.cv2.resize(frame, (int(w * scale), int(h * scale)))
        # Larger stride / scale step = fewer windows = faster
        rects, weights = self.hog.detectMultiScale(
            img, winStride=(16, 16), padding=(8, 8), scale=1.1
        )
        out: list[Detection] = []
        inv = 1.0 / scale if scale else 1.0
        for (x, y, bw, bh), weight in zip(rects, weights):
            x1, y1 = x * inv, y * inv
            x2, y2 = (x + bw) * inv, (y + bh) * inv
            out.append(
                Detection(bbox=[float(x1), float(y1), float(x2), float(y2)], confidence=float(weight))
            )
        return out


@lru_cache(maxsize=1)
def get_person_detector() -> PersonDetector:
    try:
        det = YoloPersonDetector()
        logger.info(
            "Loaded YOLO person detector model=%s imgsz=%s conf=%s",
            settings.yolo_model_name,
            settings.yolo_imgsz,
            settings.yolo_conf,
        )
        return det
    except Exception as exc:  # noqa: BLE001
        logger.warning("YOLO unavailable (%s). Falling back to OpenCV HOG.", exc)
        return HogPersonDetector()


def detector_status() -> dict[str, Any]:
    det = get_person_detector()
    return {
        "engine": det.info.name,
        "backend": det.info.backend,
        "yolo_model": settings.yolo_model_name,
        "yolo_imgsz": settings.yolo_imgsz,
        "yolo_conf": settings.yolo_conf,
        "yolo_iou": settings.yolo_iou,
        "demo_frame_stride": settings.demo_frame_stride,
        "demo_max_frames": settings.demo_max_frames,
    }


def warm_detector() -> dict[str, Any]:
    """Force-load detector into memory (startup warmup)."""
    return detector_status()
