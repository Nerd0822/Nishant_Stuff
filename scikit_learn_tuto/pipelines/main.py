"""Lesson 12: build, tune, and save one end-to-end ML pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from tutorial_utils import add_data_argument, load_telco


def make_pipeline(features):
    numeric = features.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    return Pipeline(
        [
            (
                "preprocessor",
                ColumnTransformer(
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
                ),
            ),
            ("classifier", LogisticRegression(max_iter=2_000, random_state=42)),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "telco")
    parser.add_argument("--save", type=Path, default=None, help="Optional joblib output path.")
    args = parser.parse_args()

    frame, source = load_telco(args.data)
    features = frame.drop(columns=["Churn", "customerID"], errors="ignore")
    target = frame["Churn"]
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    search = GridSearchCV(
        make_pipeline(features),
        param_grid={
            "classifier__C": [0.01, 0.1, 1.0, 10.0],
            "classifier__class_weight": [None, "balanced"],
        },
        scoring="roc_auc",
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        n_jobs=-1,
    )
    search.fit(x_train, y_train)
    model = search.best_estimator_
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    print(f"Loaded: {source}")
    print(f"Best parameters: {search.best_params_}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
    print(f"ROC AUC:  {roc_auc_score(y_test, probabilities):.3f}")
    print(classification_report(y_test, predictions, target_names=["No churn", "Churn"]))
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, args.save)
        print(f"Saved fitted pipeline to {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
