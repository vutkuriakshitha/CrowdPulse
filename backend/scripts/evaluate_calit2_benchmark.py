"""Empirical Evaluation & Benchmarking for UCI CalIt2 People Counter Dataset.

UCI Machine Learning Repository Citation:
- Dataset: CalIt2 Building People Counts (UCI ID 156 / 178)
- URL: https://archive.ics.uci.edu/dataset/156/calit2+building+people+counts
- Focus: Crowd Flow Surge Prediction, Inflow/Outflow Forecasting, and Event Surge Detection.
"""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score

BASE_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = BASE_DIR / "data" / "datasets"
REPORTS_DIR = BASE_DIR / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = DATASETS_DIR / "calit2_people_counter.csv"
EVENTS_PATH = DATASETS_DIR / "calit2_events.csv"


def load_calit2_data() -> tuple[list[dict], np.ndarray, np.ndarray, np.ndarray]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing {CSV_PATH}. Run download_calit2_dataset.py first.")

    rows = []
    inflows, outflows, net_flows = [], [], []
    is_surge = []

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            inf = float(r["inflow"])
            outf = float(r["outflow"])
            inflows.append(inf)
            outflows.append(outf)
            net_flows.append(inf - outf)
            is_surge.append(int(r["is_surge_event"]))

    return rows, np.array(inflows), np.array(outflows), np.array(is_surge)


def evaluate_forecasting(rows: list[dict], series: np.ndarray, series_name: str = "Pedestrian Inflow") -> dict:
    lags = 6  # 6 half-hours = 3-hour lookback window
    X, Y = [], []
    from datetime import datetime
    for i in range(lags, len(series) - 1):
        lag_feats = list(series[i - lags : i + 1])
        # Add hour-of-day and day-of-week covariates
        r = rows[i]
        try:
            dt = datetime.strptime(f"{r['date']} {r['time']}", "%m/%d/%y %H:%M:%S")
            hr = dt.hour + dt.minute / 60.0
            dow = dt.weekday()
        except Exception:
            hr, dow = 12.0, 3
        sin_hr = np.sin(2 * np.pi * hr / 24.0)
        cos_hr = np.cos(2 * np.pi * hr / 24.0)
        is_wknd = 1.0 if dow >= 5 else 0.0
        X.append(lag_feats + [sin_hr, cos_hr, is_wknd])
        Y.append(series[i + 1])
    X, Y = np.array(X), np.array(Y)

    # 70% Train, 30% Test (strict temporal split - zero future leakage)
    split = int(0.70 * len(X))
    X_train, X_test = X[:split], X[split:]
    Y_train, Y_test = Y[:split], Y[split:]

    # Model 1: CrowdPulse Autoregressive Ridge Forecaster
    model = Ridge(alpha=1.0)
    model.fit(X_train, Y_train)
    pred_cp = model.predict(X_test)
    pred_cp = np.maximum(0.0, pred_cp)

    # Baseline 1: Naive Persistence (y_{t+1} = y_t)
    pred_naive = X_test[:, lags]

    # Baseline 2: Rolling Average (mean of last 6 steps)
    pred_rolling = np.mean(X_test[:, : lags + 1], axis=1)

    # Metrics
    mae_cp = float(mean_absolute_error(Y_test, pred_cp))
    rmse_cp = float(np.sqrt(mean_squared_error(Y_test, pred_cp)))
    r2_cp = float(r2_score(Y_test, pred_cp))

    mae_naive = float(mean_absolute_error(Y_test, pred_naive))
    rmse_naive = float(np.sqrt(mean_squared_error(Y_test, pred_naive)))

    mae_rolling = float(mean_absolute_error(Y_test, pred_rolling))
    rmse_rolling = float(np.sqrt(mean_squared_error(Y_test, pred_rolling)))

    improvement_vs_naive = ((mae_naive - mae_cp) / max(mae_naive, 1e-6)) * 100.0
    improvement_vs_rolling = ((mae_rolling - mae_cp) / max(mae_rolling, 1e-6)) * 100.0

    min_baseline_mae = min(mae_naive, mae_rolling)
    if mae_cp < min_baseline_mae:
        winner_label = " [WINNER]"
    elif mae_cp > min_baseline_mae:
        winner_label = " [BASELINE WINS]"
    else:
        winner_label = ""

    print(f"\n--- UCI CALIT2 TIME-SERIES FORECASTING ({series_name}) ---")
    print(f"  Total Series Length:          {len(series)} intervals (15 continuous weeks)")
    print(f"  Held-out Test Steps:          {len(Y_test)} intervals")
    print(f"  CrowdPulse Forecaster MAE:    {mae_cp:.2f} persons {winner_label}")
    print(f"  CrowdPulse Forecaster RMSE:   {rmse_cp:.2f} persons")
    print(f"  CrowdPulse Forecaster R²:     {r2_cp:.3f}")
    print(f"  Naive Persistence MAE:        {mae_naive:.2f} persons (RMSE: {rmse_naive:.2f})")
    print(f"  Rolling Mean MAE:             {mae_rolling:.2f} persons (RMSE: {rmse_rolling:.2f})")
    print(f"  Error Reduction vs Naive:     {improvement_vs_naive:+.1f}%")
    print(f"  Error Reduction vs Rolling:   {improvement_vs_rolling:+.1f}%")

    return {
        "Y_test": Y_test,
        "pred_cp": pred_cp,
        "pred_naive": pred_naive,
        "mae_cp": round(mae_cp, 2),
        "rmse_cp": round(rmse_cp, 2),
        "r2_cp": round(r2_cp, 3),
        "mae_naive": round(mae_naive, 2),
        "mae_rolling": round(mae_rolling, 2),
        "gain_pct": round(improvement_vs_naive, 1),
    }


def evaluate_surge_detection(inflow: np.ndarray, is_surge_groundtruth: np.ndarray) -> dict:
    """Benchmark detection of crowd surges against UCI CalIt2 annotated ground truth events."""
    # Compute rolling Z-score anomaly detector (CrowdPulse Surge Feature)
    window = 48  # 1 day window
    rolling_mean = np.convolve(inflow, np.ones(window) / window, mode="same")
    rolling_std = np.zeros_like(rolling_mean)
    for i in range(len(inflow)):
        w = inflow[max(0, i - window // 2) : min(len(inflow), i + window // 2)]
        rolling_std[i] = np.std(w) if len(w) > 1 else 1.0
    rolling_std = np.maximum(rolling_std, 1.0)

    z_scores = (inflow - rolling_mean) / rolling_std
    surge_pred = (z_scores > 2.0).astype(int)

    prec = float(precision_score(is_surge_groundtruth, surge_pred, zero_division=0))
    rec = float(recall_score(is_surge_groundtruth, surge_pred, zero_division=0))
    f1 = float(f1_score(is_surge_groundtruth, surge_pred, zero_division=0))

    total_events = int(np.sum(is_surge_groundtruth > 0))
    detected = int(np.sum((surge_pred == 1) & (is_surge_groundtruth == 1)))

    print("\n--- UCI CALIT2 CROWD SURGE ANOMALY BENCHMARK ---")
    print(f"  Ground Truth Surge Intervals: {total_events}")
    print(f"  Correctly Detected Surges:    {detected}")
    print(f"  Surge Detection Precision:    {prec * 100:.1f}%")
    print(f"  Surge Detection Recall:       {rec * 100:.1f}%")
    print(f"  Surge Detection F1-Score:     {f1 * 100:.1f}%")

    return {
        "precision": round(prec * 100, 1),
        "recall": round(rec * 100, 1),
        "f1_score": round(f1 * 100, 1),
        "total_gt_surges": total_events,
        "z_scores": z_scores,
        "surge_pred": surge_pred,
    }


def generate_benchmark_chart(fc_results: dict, surge_results: dict, out_path: Path) -> None:
    plt.figure(figsize=(12, 7), dpi=150)

    # Subplot 1: Forecast Comparison on held-out window
    plt.subplot(2, 1, 1)
    view_slice = slice(100, 250)  # ~3 days view
    y_test = fc_results["Y_test"][view_slice]
    p_cp = fc_results["pred_cp"][view_slice]
    p_naive = fc_results["pred_naive"][view_slice]
    x_axis = np.arange(len(y_test))

    plt.plot(x_axis, y_test, label="UCI Ground Truth Inflow", color="#059669", lw=2)
    plt.plot(x_axis, p_cp, label=f"CrowdPulse Forecaster (MAE {fc_results['mae_cp']})", color="#2563eb", lw=1.8, linestyle="--")
    plt.plot(x_axis, p_naive, label=f"Naive Baseline (MAE {fc_results['mae_naive']})", color="#dc2626", lw=1.2, alpha=0.6, linestyle=":")
    plt.title("UCI Machine Learning Repository: CalIt2 People Counter Forecasting Benchmark", fontsize=11, fontweight="bold")
    plt.ylabel("Inflow Count / 30-min")
    plt.xlabel("Sampled Test Intervals (Half-Hour Steps)")
    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper right")

    # Subplot 2: Surge Anomaly Detection vs Events
    plt.subplot(2, 1, 2)
    sample_window = slice(500, 900)
    z = surge_results["z_scores"][sample_window]
    preds = surge_results["surge_pred"][sample_window]
    plt.plot(z, label="CrowdPulse Surge Z-Score Metric", color="#7c3aed", lw=1.5)
    plt.axhline(2.0, color="#f59e0b", linestyle="--", label="Surge Alert Threshold (Z=2.0)")
    plt.fill_between(range(len(preds)), 0, np.max(z), where=preds == 1, color="#ef4444", alpha=0.2, label="Surge Event Flagged")
    plt.title(f"Crowd Surge Detection Benchmark (F1: {surge_results['f1_score']}%, Recall: {surge_results['recall']}%)", fontsize=11, fontweight="bold")
    plt.ylabel("Surge Indicator")
    plt.xlabel("Interval Index")
    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close()
    print(f"\n[REPORT] Saved UCI CalIt2 benchmark figure to {out_path.name}")


def main() -> dict:
    print(f"\n{'='*75}")
    print(" UCI MACHINE LEARNING REPOSITORY: CALIT2 PEOPLE COUNTER BENCHMARK")
    print(f"{'='*75}")

    rows, inflows, outflows, surges = load_calit2_data()
    fc_results = evaluate_forecasting(rows, inflows, series_name="Pedestrian Inflow")
    surge_results = evaluate_surge_detection(inflows, surges)

    fig_path = REPORTS_DIR / "benchmark_uci_calit2.png"
    generate_benchmark_chart(fc_results, surge_results, fig_path)

    print(f"{'='*75}\n")
    return {
        "forecasting": {
            "mae_crowdpulse": fc_results["mae_cp"],
            "rmse_crowdpulse": fc_results["rmse_cp"],
            "r2_score": fc_results["r2_cp"],
            "mae_naive_baseline": fc_results["mae_naive"],
            "error_reduction_pct": fc_results["gain_pct"],
        },
        "surge_detection": {
            "precision_pct": surge_results["precision"],
            "recall_pct": surge_results["recall"],
            "f1_pct": surge_results["f1_score"],
        },
        "chart_path": str(fig_path),
    }


if __name__ == "__main__":
    main()
