"""Generate 4 test clips (300 frames each) from mall_dataset.mp4 with different start offsets,
plus one corrupt video file for Phase B verification.
"""

from pathlib import Path
import cv2

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "data" / "uploads" / "samples"
PHASE_B_DIR = SAMPLES_DIR / "phase_b"
PHASE_B_DIR.mkdir(parents=True, exist_ok=True)

SRC_VIDEO = SAMPLES_DIR / "mall_dataset.mp4"


def create_clip(src_path: Path, out_path: Path, start_frame: int, num_frames: int = 300):
    cap = cv2.VideoCapture(str(src_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {src_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    count = 0
    while count < num_frames:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        writer.write(frame)
        count += 1

    cap.release()
    writer.release()
    print(f"Created {out_path.name}: {count} frames from offset {start_frame} ({out_path.stat().st_size} bytes)")


def main():
    print(f"Reading source video from {SRC_VIDEO}")
    # 4 distinct clips with 300 frames each
    clips = [
        ("clip_zoneA.mp4", 0, 300),
        ("clip_zoneB.mp4", 400, 300),
        ("clip_zoneC.mp4", 800, 300),
        ("clip_zoneD.mp4", 1200, 300),
    ]

    for fname, offset, count in clips:
        out_file = PHASE_B_DIR / fname
        create_clip(SRC_VIDEO, out_file, offset, count)

    # Corrupt clip: invalid MP4 header & junk bytes
    corrupt_file = PHASE_B_DIR / "clip_corrupt.mp4"
    with open(corrupt_file, "wb") as f:
        f.write(b"CORRUPTED_MP4_HEADER_THIS_IS_NOT_A_VALID_H264_VIDEO_STREAM\x00\x00\x00\x18ftypisom" + b"\xFF" * 1024)
    print(f"Created {corrupt_file.name} ({corrupt_file.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
