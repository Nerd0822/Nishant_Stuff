"""Lesson 2: compare a single split with stratified cross-validation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from tutorial_utils import add_data_argument, load_telco


def make_model(features):
    numeric = features.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    preprocessor = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("one_hot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ]
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=2_000, random_state=42)),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "telco")
    args = parser.parse_args()

    frame, source = load_telco(args.data)
    features = frame.drop(columns=["Churn", "customerID"], errors="ignore")
    target = frame["Churn"]
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    model = make_model(features)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]

    print(f"Loaded: {source}")
    print("\nOne stratified 80/20 split")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
    print(f"ROC AUC:  {roc_auc_score(y_test, probabilities):.3f}")
    print(classification_report(y_test, predictions, target_names=["No churn", "Churn"]))

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(
        make_model(features), features, target, cv=cv, scoring="roc_auc", n_jobs=-1
    )
    print("Five-fold stratified ROC AUC")
    print(f"Scores: {np.array2string(scores, precision=3)}")
    print(f"Mean:   {scores.mean():.3f} (+/- {scores.std():.3f})")

    multi_scores = cross_validate(
        make_model(features),
        features,
        target,
        cv=cv,
        scoring={"accuracy": "accuracy", "roc_auc": "roc_auc", "f1": "f1"},
        n_jobs=-1,
    )
    print("\nCross-validated metrics")
    for name, values in multi_scores.items():
        if name.startswith("test_"):
            print(f"{name.removeprefix('test_'):<8}: {values.mean():.3f}")


if __name__ == "__main__":
    raise SystemExit(main())
