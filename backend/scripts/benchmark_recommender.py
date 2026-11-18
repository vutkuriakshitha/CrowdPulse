"""Benchmark recommendation models for CrowdPulse."""

from __future__ import annotations

import sys
import time

import numpy as np
from sklearn.ensemble import (
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.metrics import accuracy_score, f1_score, hamming_loss
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, ".")
from app.ai.decision.ml_recommender import ACTION_ORDER, FEATURE_NAMES, _make_training_set


def main() -> None:
    X, Y = _make_training_set(3000, seed=42)
    Xtr, Xte, Ytr, Yte = train_test_split(X, Y, test_size=0.25, random_state=42)
    scaler = StandardScaler()
    Xtr_s = scaler.fit_transform(Xtr)
    Xte_s = scaler.transform(Xte)

    models = {
        "RandomForest": MultiOutputClassifier(
            RandomForestClassifier(
                n_estimators=120,
                max_depth=10,
                min_samples_leaf=2,
                class_weight="balanced_subsample",
                random_state=42,
                n_jobs=-1,
            )
        ),
        "HistGradientBoosting": MultiOutputClassifier(
            HistGradientBoostingClassifier(
                max_depth=6,
                learning_rate=0.08,
                max_iter=120,
                random_state=42,
            )
        ),
        "GradientBoosting": MultiOutputClassifier(
            GradientBoostingClassifier(
                n_estimators=80,
                max_depth=3,
                learning_rate=0.08,
                random_state=42,
            )
        ),
    }

    print(f"features={len(FEATURE_NAMES)} actions={len(ACTION_ORDER)} train={len(Xtr)} test={len(Xte)}")
    print("-" * 78)
    results = []
    for name, model in models.items():
        t0 = time.time()
        model.fit(Xtr_s, Ytr)
        train_s = time.time() - t0
        t1 = time.time()
        pred = model.predict(Xte_s)
        infer_ms = (time.time() - t1) * 1000 / max(len(Xte), 1)
        f1_micro = f1_score(Yte, pred, average="micro", zero_division=0)
        f1_macro = f1_score(Yte, pred, average="macro", zero_division=0)
        label_acc = 1.0 - hamming_loss(Yte, pred)
        exact = accuracy_score(Yte, pred)
        results.append((name, f1_micro, f1_macro, label_acc, exact, train_s, infer_ms))
        print(
            f"{name:22s} F1_micro={f1_micro:.4f} F1_macro={f1_macro:.4f} "
            f"LabelAcc={label_acc:.4f} ExactMatch={exact:.4f} "
            f"train={train_s:.2f}s infer={infer_ms:.3f}ms/sample"
        )

    results.sort(key=lambda r: (r[1], r[3], r[4]), reverse=True)
    best = results[0][0]
    print("-" * 78)
    print(f"BEST={best}")
    # reliability note
    print("RUNTIME=all candidates are sklearn-native (no extra Windows install risk)")


if __name__ == "__main__":
    main()
