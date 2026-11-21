"""
train_model.py
----------------
Trains a state-of-the-art Gradient Boosted Decision Tree (HistGradientBoosting)
classifier that predicts whether a stock's price will go UP or DOWN the next
trading day, using a comprehensive suite of 34 multi-timeframe technical indicators.

One pooled model is trained across all 131 NSE stocks, capturing robust cross-sectional
and longitudinal market dynamics.

Run: python model/train_model.py
Produces: model/stock_model.pkl, model/metrics.json
"""

import sys
import os
import json
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.inspection import permutation_importance

sys.path.append(os.path.dirname(__file__))
from features import add_features, FEATURE_COLUMNS


def build_dataset(csv_path="data/stock_data.csv"):
    raw = pd.read_csv(csv_path, parse_dates=["Date"])
    all_frames = []
    for symbol, group in raw.groupby("Symbol"):
        group = group.sort_values("Date")
        feat = add_features(group)
        all_frames.append(feat)
    full = pd.concat(all_frames, ignore_index=True)
    full = full.dropna(subset=FEATURE_COLUMNS + ["Target"])
    return full


def train():
    print("Building feature dataset...")
    data = build_dataset()
    print(f"Dataset shape: {data.shape}")

    X = data[FEATURE_COLUMNS]
    y = data["Target"]

    # Time-aware split: train on first 80% of dates, test on last 20%
    # (never shuffle time series data for train/test split!)
    data_sorted = data.sort_values("Date")
    split_idx = int(len(data_sorted) * 0.8)
    train_df = data_sorted.iloc[:split_idx]
    test_df = data_sorted.iloc[split_idx:]

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["Target"]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["Target"]

    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # High-performance Gradient Boosted Decision Trees
    model = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.08,
        max_depth=7,
        min_samples_leaf=20,
        l2_regularization=0.3,
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, preds).tolist()
    acc = round(float(accuracy_score(y_test, preds)), 4)
    prec = round(float(precision_score(y_test, preds)), 4)
    rec = round(float(recall_score(y_test, preds)), 4)
    f1 = round(float(f1_score(y_test, preds)), 4)
    auc = round(float(roc_auc_score(y_test, proba)), 4)

    # Permutation importance on a sample of test data for fast & accurate ranking
    sample_size = min(len(X_test), 2500)
    perm_sample_idx = np.random.choice(len(X_test), sample_size, replace=False)
    X_sample = X_test.iloc[perm_sample_idx]
    y_sample = y_test.iloc[perm_sample_idx]

    perm_res = permutation_importance(
        model, X_sample, y_sample, n_repeats=3, random_state=42, n_jobs=-1
    )
    importances = perm_res.importances_mean
    importances = np.maximum(importances, 0)
    total_imp = importances.sum()
    if total_imp > 0:
        importances = importances / total_imp

    feature_importance = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in importances]))
    sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: -x[1]))

    metrics = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": auc,
        "confusion_matrix": cm,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "baseline_accuracy_majority_class": round(float(max(y_test.mean(), 1 - y_test.mean())), 4),
        "feature_importance": sorted_importance,
    }

    print("\n--- Model Performance (on held-out test set) ---")
    for k, v in metrics.items():
        if k != "feature_importance":
            print(f"{k}: {v}")

    os.makedirs("model", exist_ok=True)
    with open("model/stock_model.pkl", "wb") as f:
        pickle.dump(model, f)

    with open("model/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nSaved model -> model/stock_model.pkl")
    print("Saved metrics -> model/metrics.json")


if __name__ == "__main__":
    train()
