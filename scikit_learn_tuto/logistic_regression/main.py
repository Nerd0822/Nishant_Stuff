"""Lesson 5: classify churn and inspect probabilities."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from tutorial_utils import add_data_argument, load_telco


def make_model(features):
    numeric = features.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    preprocessor = ColumnTransformer(
        [
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric),
            (
                "categorical",
                Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("one_hot", OneHotEncoder(handle_unknown="ignore"))]),
                categorical,
            ),
        ]
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", LogisticRegression(max_iter=2_000, random_state=42))])


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
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    print(f"Loaded: {source}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
    print(f"ROC AUC:  {roc_auc_score(y_test, probabilities):.3f}")
    print(f"PR AUC:   {average_precision_score(y_test, probabilities):.3f}")
    print("\nConfusion matrix (rows=true, columns=predicted):")
    print(confusion_matrix(y_test, predictions))
    print("\nClassification report:")
    print(classification_report(y_test, predictions, target_names=["No churn", "Churn"]))
    print("Decision thresholds")
    for threshold in (0.3, 0.5, 0.7):
        threshold_predictions = (probabilities >= threshold).astype(int)
        false_positives = ((threshold_predictions == 1) & (y_test.to_numpy() == 0)).sum()
        print(
            f"  threshold={threshold:.1f}: predicted churn={threshold_predictions.sum():,}, "
            f"false positives={false_positives:,}"
        )
    print("The best threshold depends on the cost of missing a churner versus a false alarm.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
