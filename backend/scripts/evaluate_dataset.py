"""Empirical Evaluation & Ground-Truth Benchmarking Engine for CrowdPulse.

Evaluates any surveillance dataset (Kaggle Mall Dataset, Oxford Town Centre, or arbitrary CCTV):
1. Perception: Evaluates YOLOv8 detection accuracy vs Ground Truth (MAE, RMSE, R²).
2. Spatial Analytics: Tracks person flow, speed, and zone distribution (A, B, C, D).
3. Forecasting: Benchmarks Autoregressive Forecaster vs Naive Persistence Baseline.
4. Civil Engineering Risk: Classifies congestion under Fruin's Level of Service (LoS).
5. Outputs publication-quality summary tables and evaluation plots.
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
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from ultralytics import YOLO

from app.ai.perception.tracker import CentroidTracker
from app.ai.perception.zone_assigner import ZoneAssigner, zones_from_venue_dict
from app.infrastructure.persistence.seed import DEMO_ZONES

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_ground_truth(csv_path: Path) -> dict[int, int]:
    """Load frame_idx -> count mapping from CSV if available."""
    gt = {}
    if not csv_path.exists():
        return gt
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = int(row["frame_idx"])
            count = int(row["gt_count"])
            gt[idx] = count
    return gt

def evaluate_video(
    video_path: Path,
    gt_path: Path | None = None,
    stride: int = 5,
    max_frames: int | None = 300,
    model_name: str = "yolov8n.pt",
    conf: float | None = None,
) -> dict:
    from app.core.config import settings
    conf_val = conf if conf is not None else settings.yolo_conf
    print(f"\n{'='*75}")
    print(f" CROWDPULSE BENCHMARK EVALUATION: {video_path.name}")
    print(f"{'='*75}")
    print(f"Model: {model_name} | Frame Stride: {stride} | Conf: {conf_val} | Max Sampled Frames: {max_frames}")

    gt_counts = load_ground_truth(gt_path) if gt_path else {}
    has_gt = len(gt_counts) > 0
    if has_gt:
        print(f"[GROUND TRUTH] Loaded {len(gt_counts)} annotated frames from {gt_path.name}")
    else:
        print("[MODE] Arbitrary / Unlabeled CCTV video (Running unsupervised flow evaluation)")

    model = YOLO(model_name)
    tracker = CentroidTracker()
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 15.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    zones = zones_from_venue_dict(DEMO_ZONES)
    assigner = ZoneAssigner(zones, width, height)

    frame_indices = []
    yolo_counts = []
    ground_truth = []
    zone_histories = {z.code: [] for z in zones}

    t0 = time.time()
    processed = 0
    frame_idx = 0  # 1-indexed video frame counter matching ground truth

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1

        if (frame_idx - 1) % stride != 0:
            continue

        # YOLO inference using calibrated confidence and high-resolution imgsz
        results = model.predict(frame, classes=[0], conf=conf_val, imgsz=settings.yolo_imgsz, verbose=False)
        boxes = []
        if results and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()

        # Count raw YOLO detections directly rather than through the tracker
        count = len(boxes)
        yolo_counts.append(count)
        frame_indices.append(frame_idx)

        # Ground truth match - strictly aligned, raise error if beyond annotated range
        if has_gt:
            if frame_idx not in gt_counts:
                raise ValueError(
                    f"Frame {frame_idx} not found in ground truth annotations (max {max(gt_counts.keys())})"
                )
            ground_truth.append(gt_counts[frame_idx])

        # Zone counts (using raw bounding box feet)
        if len(boxes) > 0:
            feet = [((b[0] + b[2]) / 2.0, b[3]) for b in boxes]
            z_counts = assigner.count_by_zone(feet)
            for code, c in z_counts.items():
                zone_histories[code].append(c)
        else:
            for code in zone_histories:
                zone_histories[code].append(0)

        processed += 1
        if processed % 50 == 0 or (max_frames and processed == max_frames):
            print(f"  Processed {processed} frames (Current Frame {frame_idx}: YOLO={count})...", flush=True)

        if max_frames and processed >= max_frames:
            break

    cap.release()
    elapsed = time.time() - t0
    fps_eval = processed / max(elapsed, 0.001)
    print(f"\n[INFERENCE] Completed {processed} frames in {elapsed:.2f}s ({fps_eval:.1f} FPS on CPU)")

    # Print first 5 alignment triples
    if has_gt and len(ground_truth) >= 5:
        print("\n[ALIGNMENT VERIFICATION] First 5 evaluated (frame_idx, ground_truth, prediction) triples:")
        for fi, gi, pi in zip(frame_indices[:5], ground_truth[:5], yolo_counts[:5]):
            err = abs(gi - pi)
            print(f"  Frame {fi:4d}: Ground Truth = {gi:2d} | YOLOv8 Count = {pi:2d} | Delta = {err:2d}")

    # 1. Perception Accuracy Metrics
    metrics_report = {}
    if has_gt and len(ground_truth) == len(yolo_counts):
        y_true = np.array(ground_truth, dtype=float)
        y_pred = np.array(yolo_counts, dtype=float)
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))
        corr = float(np.corrcoef(y_true, y_pred)[0, 1]) if len(y_true) > 1 else 1.0

        # Unified accuracy formula clamped at 0 per frame
        acc_per_frame = np.clip(1.0 - np.abs(y_true - y_pred) / np.maximum(y_true, 1), 0.0, 1.0) * 100.0
        mean_acc = float(np.mean(acc_per_frame))
        mape = float(np.mean(np.abs(y_true - y_pred) / np.maximum(y_true, 1))) * 100.0

        metrics_report["MAE"] = round(mae, 2)
        metrics_report["RMSE"] = round(rmse, 2)
        metrics_report["R2_Score"] = round(r2, 3)
        metrics_report["Correlation"] = round(corr, 3)
        metrics_report["Relative_Accuracy_Pct"] = round(mean_acc, 1)
        metrics_report["MAPE_Pct"] = round(mape, 1)

        print("\n--- PERCEPTION BENCHMARK METRICS (YOLOv8 vs Ground Truth) ---")
        print(f"  Mean Absolute Error (MAE):       {mae:.2f} persons/frame")
        print(f"  Root Mean Squared Error (RMSE):  {rmse:.2f} persons/frame")
        print(f"  Pearson Correlation (r):          {corr:.3f}")
        print(f"  Coefficient of Det. (R²):         {r2:.3f}")
        print(f"  Mean Relative Accuracy:           {mean_acc:.1f}% (clamped >= 0% per frame)")
        print(f"  Mean Absolute Pct Error (MAPE):   {mape:.1f}%")

    # 2. Time-Series Forecasting Evaluation
    print("\n--- SPATIOTEMPORAL FORECASTING EVALUATION ---")
    ts = np.array(yolo_counts, dtype=float)
    if len(ts) >= 30:
        # Create lag features [y_{t-4}, y_{t-3}, y_{t-2}, y_{t-1}, y_t] -> y_{t+1}
        lags = 4
        X, Y = [], []
        for i in range(lags, len(ts) - 1):
            X.append(ts[i - lags : i + 1])
            Y.append(ts[i + 1])
        X, Y = np.array(X), np.array(Y)

        # 70% Train, 30% Held-out Test (Temporal Split - No frame leakage!)
        split = int(0.7 * len(X))
        X_train, X_test = X[:split], X[split:]
        Y_train, Y_test = Y[:split], Y[split:]

        # Model: Autoregressive Ridge Forecaster
        forecaster = Ridge(alpha=1.0)
        forecaster.fit(X_train, Y_train)
        pred_ml = forecaster.predict(X_test)

        # Baseline 1: Naive Persistence (Predicts current count as future count)
        pred_naive = X_test[:, -1]

        # Baseline 2: Rolling Mean (Past 5 steps average)
        pred_mean = np.mean(X_test, axis=1)

        mae_ml = float(mean_absolute_error(Y_test, pred_ml))
        mae_naive = float(mean_absolute_error(Y_test, pred_naive))
        mae_mean = float(mean_absolute_error(Y_test, pred_mean))

        min_baseline_mae = min(mae_naive, mae_mean)
        if mae_ml < min_baseline_mae:
            winner_label = "  [WINNER]"
        elif mae_ml > min_baseline_mae:
            winner_label = "  [BASELINE WINS]"
        else:
            winner_label = ""

        print(f"  Held-out Test Frames:        {len(Y_test)}")
        print(f"  CrowdPulse Autoregressive Forecaster MAE: {mae_ml:.2f} persons{winner_label}")
        print(f"  Naive Persistence Baseline MAE:          {mae_naive:.2f} persons")
        print(f"  Rolling Mean Baseline MAE:               {mae_mean:.2f} persons")
        improvement = ((mae_naive - mae_ml) / max(mae_naive, 1e-6)) * 100.0
        print(f"  Forecast Gain over Baseline:             {improvement:+.1f}%")

        metrics_report["Forecaster_MAE"] = round(mae_ml, 2)
        metrics_report["Naive_Baseline_MAE"] = round(mae_naive, 2)
        metrics_report["Forecast_Gain_Pct"] = round(improvement, 1)

    # 3. Zone Distribution & Fruin LoS Breakdown
    print("\n--- FRUIN LEVEL OF SERVICE (LoS) ZONE ANALYSIS ---")
    zone_peaks = {code: max(counts) if counts else 0 for code, counts in zone_histories.items()}
    zone_means = {code: float(np.mean(counts)) if counts else 0.0 for code, counts in zone_histories.items()}

    for code in sorted(zone_peaks.keys()):
        peak = zone_peaks[code]
        mean = zone_means[code]
        # Fruin proxy: density estimate
        los = "LoS A/B (Free)" if peak < 10 else ("LoS C/D (Moderate)" if peak < 25 else "LoS E/F (Severe)")
        print(f"  Zone {code}: Peak Count = {peak:2d} | Mean Count = {mean:4.1f} | Risk Status = {los}")

    # 4. Generate Publication-Quality Figure
    fig_path = REPORTS_DIR / f"benchmark_{video_path.stem}.png"
    plt.figure(figsize=(11, 6), dpi=150)

    plt.subplot(2, 1, 1)
    if has_gt:
        plt.plot(frame_indices, ground_truth, label="Ground Truth (Human Annotated)", color="#10b981", lw=2)
    plt.plot(frame_indices, yolo_counts, label="CrowdPulse YOLOv8 Detection", color="#2563eb", lw=1.8, linestyle="--")
    plt.title(f"Crowd Counting Benchmark: {video_path.name}", fontsize=12, fontweight="bold")
    plt.xlabel("Sampled Frame Number")
    plt.ylabel("Pedestrian Count")
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.subplot(2, 1, 2)
    for code, series in zone_histories.items():
        plt.plot(frame_indices, series, label=f"Zone {code}", lw=1.5)
    plt.title("Spatial Zone Distribution Over Time (Zones A, B, C, D)", fontsize=11, fontweight="bold")
    plt.xlabel("Sampled Frame Number")
    plt.ylabel("Zone Count")
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.savefig(str(fig_path))
    plt.close()
    print(f"\n[REPORT] Saved benchmark evaluation chart to: {fig_path.name}")
    print(f"{'='*75}\n")

    return {
        "video": video_path.name,
        "processed_frames": processed,
        "fps_eval": round(fps_eval, 1),
        "metrics": metrics_report,
        "zone_peaks": zone_peaks,
        "chart_path": str(fig_path),
        "total_gt_pedestrians": int(np.sum(ground_truth)) if ground_truth else 0,
        "first_5_triples": list(zip(frame_indices[:5], ground_truth[:5], yolo_counts[:5])),
    }


def main():
    parser = argparse.ArgumentParser(description="CrowdPulse Ground-Truth Evaluation Benchmark")
    parser.add_argument("--video", default="data/uploads/samples/mall_dataset.mp4")
    parser.add_argument("--gt", default=None, help="Optional ground truth CSV (e.g. data/datasets/mall_groundtruth.csv)")
    parser.add_argument("--stride", type=int, default=10)
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--quick", action="store_true", help="Quick mode (stride 10 across video)")
    parser.add_argument("--full", action="store_true", help="Full mode (stride 1, all 2000 frames)")
    parser.add_argument("--conf", type=float, default=None, help="YOLO confidence threshold (defaults to settings.yolo_conf)")
    args = parser.parse_args()

    v_path = Path(args.video)
    if not v_path.exists():
        v_path = BASE_DIR / args.video
    if not v_path.exists():
        raise FileNotFoundError(f"Video not found: {args.video}")

    gt_path = None
    if args.gt:
        p = Path(args.gt)
        if not p.exists():
            p = BASE_DIR / args.gt
        if p.exists():
            gt_path = p
    elif "mall" in v_path.name.lower():
        default_gt = BASE_DIR / "data" / "datasets" / "mall_groundtruth.csv"
        if default_gt.exists():
            gt_path = default_gt

    stride = args.stride
    max_frames = args.max_frames
    if args.quick:
        stride = 10
        max_frames = None
    elif args.full:
        stride = 1
        max_frames = None

    evaluate_video(v_path, gt_path, stride=stride, max_frames=max_frames, conf=args.conf)


if __name__ == "__main__":
    main()
