"""Lesson 14: find unusual transactions with Isolation Forest."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from tutorial_utils import add_data_argument, load_dataframe, require_columns


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "credit_card")
    parser.add_argument("--sample", type=int, default=20_000, help="Maximum rows for a fast lesson.")
    args = parser.parse_args()

    frame, source = load_dataframe("credit_card", args.data)
    require_columns(frame, ["Class"], "Credit-card dataset")
    frame["Class"] = pd.to_numeric(frame["Class"], errors="coerce")
    frame = frame.dropna(subset=["Class"])
    frame = frame.sample(n=min(args.sample, len(frame)), random_state=42)
    target = frame["Class"].astype(int)
    features = frame.drop(columns=["Class"])
    if target.nunique() < 2:
        raise ValueError("The sample must contain both fraud and non-fraud rows.")

    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    preprocessor = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    x_train_processed = preprocessor.fit_transform(x_train)
    x_test_processed = preprocessor.transform(x_test)

    model = IsolationForest(n_estimators=100, contamination="auto", random_state=42, n_jobs=-1)
    model.fit(x_train_processed)
    predictions = (model.predict(x_test_processed) == -1).astype(int)
    anomaly_scores = -model.score_samples(x_test_processed)

    print(f"Loaded: {source}")
    print(f"Sampled rows: {len(frame):,}; known fraud rows: {target.sum():,}")
    print(f"Detected anomalies: {predictions.sum():,}")
    print(f"ROC AUC (anomaly score): {roc_auc_score(y_test, anomaly_scores):.3f}")
    print(f"Average precision:      {average_precision_score(y_test, anomaly_scores):.3f}")
    print(classification_report(y_test, predictions, target_names=["Legitimate", "Fraud"]))
    print("This is a teaching baseline. Real fraud systems need cost controls and monitoring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
