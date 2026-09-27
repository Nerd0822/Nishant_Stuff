"""Lesson 13: handle an imbalanced target with weights and better metrics."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from tutorial_utils import add_data_argument, load_telco


def make_model(features, class_weight):
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
    return Pipeline(
        [("preprocessor", preprocessor), ("classifier", LogisticRegression(max_iter=2_000, class_weight=class_weight, random_state=42))]
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
    print(f"Loaded: {source}")
    print(f"Class counts: {target.value_counts().to_dict()}")
    for class_weight in (None, "balanced"):
        model = make_model(features, class_weight)
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        print(f"\nclass_weight={class_weight}")
        print(f"  balanced accuracy: {balanced_accuracy_score(y_test, predictions):.3f}")
        print(f"  ROC AUC:           {roc_auc_score(y_test, probabilities):.3f}")
        print(f"  average precision: {average_precision_score(y_test, probabilities):.3f}")
        print("  confusion matrix:")
        print(confusion_matrix(y_test, predictions))
        print(classification_report(y_test, predictions, target_names=["No churn", "Churn"]))
    print("Class weights change the training objective, not the meaning of the test labels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
