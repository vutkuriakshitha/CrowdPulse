"""Edge perception agent: YOLO + ByteTrack → Redis Streams.

This module is designed for NVIDIA Jetson / x86 GPU edge nodes.
It degrades to a synthetic publisher when ultralytics is unavailable,
keeping the cloud twin pipeline exercisable in CI/dev.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from typing import Any

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None


def publish_synthetic(redis_url: str, stream: str, camera_id: str, fps: int = 5) -> None:
    if redis is None:
        raise RuntimeError("redis package required")
    client = redis.from_url(redis_url)
    interval = 1.0 / max(fps, 1)
    track_id = 1
    print(f"[edge] synthetic publisher camera={camera_id} → {stream}")
    while True:
        n = random.randint(8, 25)
        detections = []
        for i in range(n):
            detections.append(
                {
                    "camera_id": camera_id,
                    "track_id": track_id + i,
                    "bbox": [
                        random.uniform(0, 1000),
                        random.uniform(0, 700),
                        random.uniform(20, 80),
                        random.uniform(40, 160),
                    ],
                    "confidence": round(random.uniform(0.55, 0.98), 3),
                    "timestamp": time.time(),
                }
            )
        track_id += n
        client.xadd(stream, {"payload": json.dumps(detections)}, maxlen=5000, approximate=True)
        time.sleep(interval)


def run_yolo(source: str, camera_id: str, redis_url: str, stream: str) -> None:
    """Real YOLO path — requires ultralytics + opencv installed on edge image."""
    from ultralytics import YOLO  # type: ignore
    import cv2

    if redis is None:
        raise RuntimeError("redis package required")
    client = redis.from_url(redis_url)
    model = YOLO("yolo11n.pt")
    cap = cv2.VideoCapture(0 if source == "0" else source)
    print(f"[edge] YOLO publisher camera={camera_id} source={source}")
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.2)
            continue
        results = model.track(frame, persist=True, classes=[0], verbose=False)
        detections: list[dict[str, Any]] = []
        if results and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].tolist()
                conf = float(boxes.conf[i])
                tid = int(boxes.id[i]) if boxes.id is not None else i
                detections.append(
                    {
                        "camera_id": camera_id,
                        "track_id": tid,
                        "bbox": xyxy,
                        "confidence": conf,
                        "timestamp": time.time(),
                    }
                )
        client.xadd(stream, {"payload": json.dumps(detections)}, maxlen=5000, approximate=True)


def main():
    parser = argparse.ArgumentParser(description="CrowdPulse Edge Publisher")
    parser.add_argument("--camera-id", default="cam-01")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0")
    parser.add_argument("--stream", default="cp:detections")
    parser.add_argument("--source", default="synthetic", help="synthetic | 0 | rtsp://...")
    parser.add_argument("--fps", type=int, default=5)
    args = parser.parse_args()

    if args.source == "synthetic":
        publish_synthetic(args.redis_url, args.stream, args.camera_id, args.fps)
    else:
        run_yolo(args.source, args.camera_id, args.redis_url, args.stream)


if __name__ == "__main__":
    main()
