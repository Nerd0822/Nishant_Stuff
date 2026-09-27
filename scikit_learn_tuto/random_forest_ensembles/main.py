"""Lesson 7: compare a single tree with bagging and boosting."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from tutorial_utils import add_data_argument, load_telco


def make_preprocessor(features):
    numeric = features.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    return ColumnTransformer(
        [
            ("numeric", SimpleImputer(strategy="median"), numeric),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("one_hot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical,
            ),
        ]
    )


def make_model(features, estimator):
    return Pipeline([("preprocessor", make_preprocessor(features)), ("classifier", estimator)])


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

    models = {
        "Decision tree": DecisionTreeClassifier(max_depth=6, random_state=42),
        "Random forest": RandomForestClassifier(
            n_estimators=250, min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "Gradient boosting": GradientBoostingClassifier(random_state=42),
    }
    print(f"Loaded: {source}")
    for name, estimator in models.items():
        model = make_model(features, estimator)
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, 1]
        print(
            f"{name:<18} accuracy={accuracy_score(y_test, predictions):.3f} "
            f"f1={f1_score(y_test, predictions):.3f} "
            f"roc_auc={roc_auc_score(y_test, probabilities):.3f}"
        )
    print("\nBagging averages many trees; boosting adds trees sequentially to correct errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
