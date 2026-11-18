"""Download and prepare the official CUHK Mall Crowd Dataset for CrowdPulse.

Dataset details:
- 2,000 video frames (640x480) from public surveillance CCTV.
- Over 60,000 annotated pedestrian heads in mall_gt.mat.
- Official research source: http://personal.ie.cuhk.edu.hk/~ccloy/downloads_mall_dataset.html
  (Mirrored on Kaggle as fedesoriano/mall-dataset and tthien/crowd-counting).
"""

from __future__ import annotations

import csv
from pathlib import Path
import urllib.request
import zipfile

import cv2
import numpy as np
import scipy.io

DATASET_URL = "http://personal.ie.cuhk.edu.hk/~ccloy/files/datasets/mall_dataset.zip"
BASE_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = BASE_DIR / "data" / "datasets"
SAMPLES_DIR = BASE_DIR / "data" / "uploads" / "samples"
ZIP_PATH = DATASETS_DIR / "mall_dataset.zip"
EXTRACT_DIR = DATASETS_DIR / "mall_dataset"
OUT_VIDEO_PATH = SAMPLES_DIR / "mall_dataset.mp4"
OUT_CSV_PATH = DATASETS_DIR / "mall_groundtruth.csv"


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 80 * 1024 * 1024:
        print(f"[CACHE] Using existing zip: {dest.name} ({dest.stat().st_size // (1024*1024)} MB)")
        return

    print(f"[DOWNLOAD] Fetching {url} -> {dest.name} (~91.8 MB)...")

    def report(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        mb = (count * block_size) / (1024 * 1024)
        if count % 200 == 0:
            print(f"  Downloaded {mb:.1f} MB ({percent}%)", end="\r", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=report)
    print(f"\n[DOWNLOAD] Complete: {dest.name}")


def extract_zip(zip_path: Path, target_dir: Path) -> None:
    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"[CACHE] Dataset already extracted in {target_dir}")
        return
    print(f"[EXTRACT] Unzipping {zip_path.name}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)
    print(f"[EXTRACT] Done extracting to {target_dir}")


def build_mp4_video(frames_dir: Path, out_path: Path, fps: int = 15) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Frames can be in frames_dir directly or inside a frames/ subfolder
    frame_files = sorted(frames_dir.glob("*.jpg"))
    if not frame_files:
        sub = list(frames_dir.rglob("*.jpg"))
        frame_files = sorted(sub)

    if not frame_files:
        raise FileNotFoundError(f"No JPG frames found in {frames_dir}")

    print(f"[VIDEO] Compiling {len(frame_files)} frames into {out_path.name} at {fps} FPS...")
    first = cv2.imread(str(frame_files[0]))
    h, w = first.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, float(fps), (w, h))

    for idx, fpath in enumerate(frame_files):
        img = cv2.imread(str(fpath))
        if img is not None:
            writer.write(img)
        if idx % 400 == 0:
            print(f"  Processed {idx}/{len(frame_files)} frames...", end="\r", flush=True)

    writer.release()
    print(f"\n[VIDEO] Created {out_path.name} ({out_path.stat().st_size // (1024*1024)} MB)")
    return out_path


def parse_ground_truth(mat_path: Path, out_csv: Path) -> int:
    """Extract ground-truth head coordinates and frame counts from mall_gt.mat."""
    if not mat_path.exists():
        candidates = list(mat_path.parent.rglob("mall_gt.mat"))
        if candidates:
            mat_path = candidates[0]
        else:
            print(f"[WARN] {mat_path.name} not found, skipping CSV export")
            return 0

    print(f"[GT] Parsing ground truth from {mat_path.name}...")
    data = scipy.io.loadmat(str(mat_path))
    # 'count' contains [2000, 1] frame counts
    counts = data.get("count", [])
    # 'frame' cell array contains head coordinates [[x, y], ...] per frame
    frame_cells = data.get("frame", [])

    rows = []
    total_heads = 0
    num_frames = len(counts)

    for i in range(num_frames):
        c = int(counts[i][0]) if i < len(counts) else 0
        total_heads += c
        # Get heads coords
        coords_str = ""
        if i < len(frame_cells):
            try:
                cell = frame_cells[i][0][0][0]
                if isinstance(cell, np.ndarray) and len(cell.shape) == 2:
                    coords = [[round(float(pt[0]), 1), round(float(pt[1]), 1)] for pt in cell]
                    coords_str = ";".join(f"{x},{y}" for x, y in coords)
            except Exception:
                pass
        rows.append({"frame_idx": i + 1, "gt_count": c, "heads": coords_str})

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["frame_idx", "gt_count", "heads"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[GT] Exported {len(rows)} frames with {total_heads} pedestrian annotations to {out_csv.name}")
    return len(rows)


def main():
    download_file(DATASET_URL, ZIP_PATH)
    extract_zip(ZIP_PATH, EXTRACT_DIR)
    parse_ground_truth(EXTRACT_DIR / "mall_gt.mat", OUT_CSV_PATH)

    # Find frames directory
    frames_dir = EXTRACT_DIR / "frames"
    if not frames_dir.exists():
        sub_frames = list(EXTRACT_DIR.rglob("seq_*.jpg"))
        if sub_frames:
            frames_dir = sub_frames[0].parent
        else:
            frames_dir = EXTRACT_DIR

    build_mp4_video(frames_dir, OUT_VIDEO_PATH, fps=15)
    print("\n[SUCCESS] Kaggle/CUHK Mall Dataset is ready for CrowdPulse!")
    print(f"  Video: {OUT_VIDEO_PATH}")
    print(f"  Ground Truth: {OUT_CSV_PATH}")


if __name__ == "__main__":
    main()
