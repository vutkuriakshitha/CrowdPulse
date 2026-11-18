"""Day 20 — generate sparse / medium / dense synthetic CCTV sample clips."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "uploads" / "samples"

# (filename, people_count, frames, seed)
PACK = (
    ("sparse_crowd.mp4", 3, 45, 11),
    ("medium_crowd.mp4", 8, 60, 22),
    ("dense_crowd.mp4", 18, 75, 33),
)


def _write_clip(path: Path, *, n_people: int, n_frames: int, seed: int) -> Path:
    w, h, fps = 640, 360, 15
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    rng = np.random.default_rng(seed)
    people = []
    for _ in range(n_people):
        people.append(
            {
                "x": int(rng.integers(30, w - 70)),
                "y": int(rng.integers(70, h - 130)),
                "vx": float(rng.choice([-2.5, -1.5, -1, 1, 1.5, 2.5])),
                "vy": float(rng.choice([-1, -0.5, 0, 0.5, 1])),
            }
        )

    for _t in range(n_frames):
        frame = np.full((h, w, 3), 38, dtype=np.uint8)
        cv2.rectangle(frame, (0, h // 2), (w, h), (52, 52, 52), -1)
        # simple zone guides (visual only)
        cv2.line(frame, (w // 3, 0), (w // 3, h), (70, 70, 80), 1)
        cv2.line(frame, (2 * w // 3, 0), (2 * w // 3, h), (70, 70, 80), 1)
        for p in people:
            p["x"] = int((p["x"] + p["vx"]) % (w - 40))
            p["y"] = int(np.clip(p["y"] + p["vy"], 50, h - 110))
            x, y = int(p["x"]), int(p["y"])
            cv2.rectangle(frame, (x, y), (x + 26, y + 68), (195, 198, 210), -1)
            cv2.circle(frame, (x + 13, y - 10), 11, (215, 195, 175), -1)
        writer.write(frame)
    writer.release()
    return path


def main() -> list[Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Keep legacy one-click name in sync with medium density
    written: list[Path] = []
    for name, n_people, n_frames, seed in PACK:
        path = _write_clip(OUT_DIR / name, n_people=n_people, n_frames=n_frames, seed=seed)
        written.append(path)
        print(f"wrote {path.name} people={n_people} frames={n_frames}")

    # Alias used by pipeline default
    medium = OUT_DIR / "medium_crowd.mp4"
    synthetic = OUT_DIR / "synthetic_crowd.mp4"
    if medium.exists():
        synthetic.write_bytes(medium.read_bytes())
        print(f"wrote {synthetic.name} (alias of medium_crowd.mp4)")
        written.append(synthetic)
    return written


if __name__ == "__main__":
    main()
