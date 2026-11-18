"""Detector & Tracker Comparison Benchmark on CUHK Mall Dataset.

Runs empirical evaluations across YOLOv8 variants (nano, small, medium)
at varying confidence thresholds (0.10 vs 0.25) and benchmarks ByteTrack
vs CrowdPulse CentroidTracker.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
import time

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import cv2
import numpy as np
from ultralytics import YOLO

from app.ai.perception.detector import Detection
from app.ai.perception.tracker import CentroidTracker
from scripts.evaluate_dataset import evaluate_video, BASE_DIR

VIDEO_PATH = BASE_DIR / "data" / "uploads" / "samples" / "mall_dataset.mp4"
GT_PATH = BASE_DIR / "data" / "datasets" / "mall_groundtruth.csv"


def run_quick_comparisons() -> list[dict]:
    """Step 1: Run evaluate_dataset.py logic with stride 10 across 6 configurations."""
    models = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]
    confs = [0.10, 0.25]
    results = []

    print("\n" + "=" * 80)
    print("STEP 1: COMPARING DETECTORS ON REAL MALL BENCHMARK (--quick, stride 10, imgsz 960)")
    print("=" * 80)

    for model_name in models:
        for conf in confs:
            print(f"\n>>> Running Evaluation: Model={model_name} | Conf={conf:.2f} | Imgsz=960 | Stride=10 <<<")
            t_start = time.time()
            try:
                res = evaluate_video(
                    video_path=VIDEO_PATH,
                    gt_path=GT_PATH,
                    stride=10,
                    max_frames=None,
                    model_name=model_name,
                    conf=conf,
                )
                wall_time = time.time() - t_start
                m = res["metrics"]
                record = {
                    "model": model_name,
                    "conf": conf,
                    "mae": m.get("MAE"),
                    "rmse": m.get("RMSE"),
                    "r2": m.get("R2_Score"),
                    "rel_acc": m.get("Relative_Accuracy_Pct"),
                    "fps": res.get("fps_eval"),
                    "frames": res.get("processed_frames"),
                    "wall_time_s": round(wall_time, 2),
                }
                results.append(record)
            except Exception as e:
                print(f"[ERROR] Failed evaluating {model_name} with conf {conf}: {e}")
                results.append({
                    "model": model_name,
                    "conf": conf,
                    "error": str(e),
                })

    # Print summary table
    print("\n" + "=" * 90)
    print("FINAL STEP 1 COMPARISON TABLE (--quick, stride 10, 200 sampled frames, imgsz 960)")
    print("=" * 90)
    header = f"{'Model':<12} | {'Conf':<6} | {'MAE (ppl)':<10} | {'RMSE':<8} | {'R²':<8} | {'Rel Acc %':<10} | {'FPS (CPU)':<10} | {'Runtime (s)':<12}"
    print(header)
    print("-" * len(header))
    for r in results:
        if "error" in r:
            print(f"{r['model']:<12} | {r['conf']:<6.2f} | ERROR: {r['error']}")
        else:
            print(
                f"{r['model']:<12} | {r['conf']:<6.2f} | {r['mae']:<10.2f} | {r['rmse']:<8.2f} | "
                f"{r['r2']:<8.3f} | {r['rel_acc']:<10.1f} | {r['fps']:<10.1f} | {r['wall_time_s']:<12.1f}"
            )
    print("=" * 90 + "\n")
    return results


def run_full_evaluation(model_name: str, conf: float) -> dict:
    """Step 2: Run evaluate_dataset.py with --full (stride 1, all 2000 frames) on best model."""
    print("\n" + "=" * 80)
    print(f"STEP 2: FULL EVALUATION ON BEST MODEL ({model_name}, conf={conf:.2f}, all 2000 frames, stride 1)")
    print("=" * 80)
    t0 = time.time()
    res = evaluate_video(
        video_path=VIDEO_PATH,
        gt_path=GT_PATH,
        stride=1,
        max_frames=None,
        model_name=model_name,
        conf=conf,
    )
    total_runtime = time.time() - t0
    m = res["metrics"]
    print("\n" + "=" * 80)
    print("FULL RUN SUMMARY:")
    print(f"  Model:                 {model_name}")
    print(f"  Confidence Threshold:  {conf:.2f}")
    print(f"  Processed Frames:      {res['processed_frames']}")
    print(f"  Total Runtime:         {total_runtime:.2f} seconds ({total_runtime / 60:.2f} minutes)")
    print(f"  Inference Speed:       {res['fps_eval']} FPS on CPU")
    print(f"  MAE:                   {m.get('MAE')} persons/frame")
    print(f"  RMSE:                  {m.get('RMSE')} persons/frame")
    print(f"  R² Score:              {m.get('R2_Score')}")
    print(f"  Relative Accuracy:     {m.get('Relative_Accuracy_Pct')}%")
    print(f"  MAPE:                  {m.get('MAPE_Pct')}%")
    print("=" * 80 + "\n")
    return {
        "model": model_name,
        "conf": conf,
        "runtime_s": round(total_runtime, 2),
        "fps": res["fps_eval"],
        "metrics": m,
    }


def evaluate_tracker_inflation(
    video_path: Path,
    max_frames: int = 300,
    stride: int = 1,
    model_name: str = "yolov8n.pt",
    conf: float = 0.10,
    imgsz: int = 960,
) -> dict:
    """Compare unique track IDs vs mean per-frame count for CentroidTracker vs ByteTrack."""
    print(f"\n--- Testing Trackers: max_frames={max_frames}, stride={stride}, model={model_name}, conf={conf} ---")

    # 1. CentroidTracker run
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    yolo_detector = YOLO(model_name)
    ct_tracker = CentroidTracker(max_lost=20, iou_threshold=0.15, dist_threshold=60.0)
    ct_unique_ids = set()
    ct_counts = []

    frame_idx = 0
    sampled = 0
    t0_ct = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx > max_frames:
            break
        if (frame_idx - 1) % stride != 0:
            continue

        sampled += 1
        # Predict detections
        res = yolo_detector.predict(frame, classes=[0], conf=conf, imgsz=imgsz, verbose=False)
        dets = []
        if res and res[0].boxes is not None:
            boxes = res[0].boxes.xyxy.cpu().numpy()
            confs = res[0].boxes.conf.cpu().numpy()
            for b, c in zip(boxes, confs):
                dets.append(Detection(bbox=b.tolist(), confidence=float(c)))

        active_tracks = ct_tracker.update(dets)
        for t in active_tracks:
            ct_unique_ids.add(t.track_id)
        ct_counts.append(len(active_tracks))

    cap.release()
    elapsed_ct = time.time() - t0_ct
    ct_mean_count = float(np.mean(ct_counts)) if ct_counts else 0.0
    ct_unique_total = len(ct_unique_ids)
    ct_inflation = ct_unique_total / max(ct_mean_count, 1e-6)

    # 2. ByteTrack run
    cap = cv2.VideoCapture(str(video_path))
    bt_model = YOLO(model_name)  # fresh model instance to ensure clear tracker state
    bt_unique_ids = set()
    bt_counts = []

    frame_idx = 0
    sampled_bt = 0
    t0_bt = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx > max_frames:
            break
        if (frame_idx - 1) % stride != 0:
            continue

        sampled_bt += 1
        res = bt_model.track(
            frame,
            tracker="bytetrack.yaml",
            persist=True,
            classes=[0],
            conf=conf,
            imgsz=imgsz,
            verbose=False,
        )
        if res and res[0].boxes is not None and res[0].boxes.id is not None:
            ids = res[0].boxes.id.int().cpu().tolist()
            bt_unique_ids.update(ids)
            bt_counts.append(len(ids))
        else:
            bt_counts.append(0)

    cap.release()
    elapsed_bt = time.time() - t0_bt
    bt_mean_count = float(np.mean(bt_counts)) if bt_counts else 0.0
    bt_unique_total = len(bt_unique_ids)
    bt_inflation = bt_unique_total / max(bt_mean_count, 1e-6)

    return {
        "stride": stride,
        "frames_evaluated": sampled,
        "centroid_tracker": {
            "unique_ids": ct_unique_total,
            "mean_count": round(ct_mean_count, 2),
            "inflation_ratio": round(ct_inflation, 2),
            "elapsed_s": round(elapsed_ct, 2),
            "fps": round(sampled / max(elapsed_ct, 0.001), 1),
        },
        "bytetrack": {
            "unique_ids": bt_unique_total,
            "mean_count": round(bt_mean_count, 2),
            "inflation_ratio": round(bt_inflation, 2),
            "elapsed_s": round(elapsed_bt, 2),
            "fps": round(sampled_bt / max(elapsed_bt, 0.001), 1),
        },
    }


def run_tracker_benchmark() -> list[dict]:
    """Step 3: Test ByteTrack vs CentroidTracker on first 300 frames at stride 1 and 4."""
    print("\n" + "=" * 80)
    print("STEP 3: BENCHMARKING CENTROIDTRACKER VS BYTETRACK (First 300 frames of mall_dataset.mp4)")
    print("=" * 80)
    results = []
    for stride in [1, 4]:
        res = evaluate_tracker_inflation(
            video_path=VIDEO_PATH,
            max_frames=300,
            stride=stride,
            model_name="yolov8n.pt",
            conf=0.10,
            imgsz=960,
        )
        results.append(res)
        ct = res["centroid_tracker"]
        bt = res["bytetrack"]
        print(f"\n[RESULTS: Stride {stride} ({res['frames_evaluated']} frames sampled)]")
        print(f"  CentroidTracker: Unique IDs = {ct['unique_ids']:3d} | Mean Count/frame = {ct['mean_count']:5.2f} | Inflation = {ct['inflation_ratio']:5.2f}x | Speed = {ct['fps']} FPS")
        print(f"  ByteTrack:       Unique IDs = {bt['unique_ids']:3d} | Mean Count/frame = {bt['mean_count']:5.2f} | Inflation = {bt['inflation_ratio']:5.2f}x | Speed = {bt['fps']} FPS")
        if ct["unique_ids"] < bt["unique_ids"]:
            print(f"  -> CentroidTracker inflates LESS ({ct['unique_ids']} vs {bt['unique_ids']} IDs, factor {bt['unique_ids']/max(ct['unique_ids'],1):.1f}x fewer switches)")
        elif bt["unique_ids"] < ct["unique_ids"]:
            print(f"  -> ByteTrack inflates LESS ({bt['unique_ids']} vs {ct['unique_ids']} IDs, factor {ct['unique_ids']/max(bt['unique_ids'],1):.1f}x fewer switches)")
        else:
            print("  -> Both produced identical unique IDs count.")

    # Table output
    print("\n" + "=" * 90)
    print("TRACKER INFLATION BENCHMARK SUMMARY TABLE (First 300 frames of mall_dataset.mp4)")
    print("=" * 90)
    print(f"{'Stride':<8} | {'Tracker':<18} | {'Sampled':<8} | {'Unique IDs':<12} | {'Mean Count':<12} | {'Inflation Ratio':<16} | {'FPS (CPU)':<10}")
    print("-" * 90)
    for r in results:
        s = r["stride"]
        sf = r["frames_evaluated"]
        ct = r["centroid_tracker"]
        bt = r["bytetrack"]
        print(f"{s:<8} | {'CentroidTracker':<18} | {sf:<8} | {ct['unique_ids']:<12} | {ct['mean_count']:<12.2f} | {ct['inflation_ratio']:<16.2f} | {ct['fps']:<10.1f}")
        print(f"{s:<8} | {'ByteTrack':<18} | {sf:<8} | {bt['unique_ids']:<12} | {bt['mean_count']:<12.2f} | {bt['inflation_ratio']:<16.2f} | {bt['fps']:<10.1f}")
        print("-" * 90)
    print("=" * 90 + "\n")
    return results


def main():
    parser = argparse.ArgumentParser(description="Detector and Tracker Comparison Benchmark")
    parser.add_argument("--step", choices=["1", "2", "3", "all"], default="all", help="Which step to run")
    parser.add_argument("--best-model", default=None, help="Override best model name for step 2")
    parser.add_argument("--best-conf", type=float, default=None, help="Override best conf for step 2")
    args = parser.parse_args()

    quick_results = None
    if args.step in ["1", "all"]:
        quick_results = run_quick_comparisons()

    best_model = args.best_model
    best_conf = args.best_conf

    if quick_results and (best_model is None or best_conf is None):
        # Pick best by MAE
        valid = [r for r in quick_results if "mae" in r and r["mae"] is not None]
        if valid:
            best_entry = min(valid, key=lambda x: x["mae"])
            best_model = best_entry["model"]
            best_conf = best_entry["conf"]
            print(f"\n[WINNER SELECTION] Best model by lowest MAE is: {best_model} @ conf={best_conf:.2f} (MAE: {best_entry['mae']:.2f})")

    if args.step in ["2", "all"]:
        if not best_model:
            best_model = "yolov8m.pt"
            best_conf = 0.10
        run_full_evaluation(best_model, best_conf)

    if args.step in ["3", "all"]:
        run_tracker_benchmark()


if __name__ == "__main__":
    main()
