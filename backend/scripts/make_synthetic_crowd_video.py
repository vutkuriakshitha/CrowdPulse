"""Create a short synthetic crowd-like clip for detector pipeline tests."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def main() -> Path:
    out_dir = Path(__file__).resolve().parents[1] / "data" / "uploads" / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "synthetic_crowd.mp4"

    w, h, fps, n = 640, 360, 15, 60
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    rng = np.random.default_rng(7)

    # predefine pedestrian-like rectangles
    people = []
    for i in range(8):
        people.append(
            {
                "x": int(rng.integers(40, w - 80)),
                "y": int(rng.integers(80, h - 140)),
                "vx": float(rng.choice([-2, -1, 1, 2])),
                "vy": float(rng.choice([-1, 0, 1])),
            }
        )

    for t in range(n):
        frame = np.full((h, w, 3), 40, dtype=np.uint8)
        # floor
        cv2.rectangle(frame, (0, h // 2), (w, h), (55, 55, 55), -1)
        for p in people:
            p["x"] = int((p["x"] + p["vx"]) % (w - 40))
            p["y"] = int(np.clip(p["y"] + p["vy"], 60, h - 120))
            x, y = p["x"], p["y"]
            # body
            cv2.rectangle(frame, (x, y), (x + 28, y + 70), (200, 200, 210), -1)
            # head
            cv2.circle(frame, (x + 14, y - 12), 12, (220, 200, 180), -1)
        writer.write(frame)
    writer.release()
    print(out)
    return out


if __name__ == "__main__":
    main()
