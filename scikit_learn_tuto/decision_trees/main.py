"""Lesson 6: grow and prune a decision tree."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from tutorial_utils import add_data_argument, load_dataframe

PIMA_COLUMNS = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin",
    "BMI", "DiabetesPedigreeFunction", "Age", "Outcome",
]


def load_pima(path):
    frame, source = load_dataframe("pima", path)
    frame = frame.loc[:, ~frame.columns.astype(str).str.lower().str.startswith("unnamed")]
    target_candidates = ("Outcome", "outcome", "diabetes", "class", "target")
    if not any(column in frame.columns for column in target_candidates):
        if frame.shape[1] == 9:
            frame.columns = PIMA_COLUMNS
        elif frame.shape[1] == 8:
            frame.columns = PIMA_COLUMNS[:-1] + ["Outcome"]
        else:
            raise ValueError("Could not find a Pima target. Rename it to 'Outcome'.")
    target_name = next(column for column in target_candidates if column in frame.columns)
    frame = frame.rename(columns={target_name: "Outcome"})
    frame = frame.apply(pd.to_numeric, errors="coerce")
    frame["Outcome"] = frame["Outcome"].astype(int)
    return frame, source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "pima")
    args = parser.parse_args()

    frame, source = load_pima(args.data)
    target = frame.pop("Outcome")
    x_train, x_test, y_train, y_test = train_test_split(
        frame, target, test_size=0.2, random_state=42, stratify=target
    )
    pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("tree", DecisionTreeClassifier(random_state=42))]
    )
    search = GridSearchCV(
        pipeline,
        param_grid={
            "tree__max_depth": [2, 3, 4, 5, None],
            "tree__min_samples_leaf": [1, 5, 10, 20],
            "tree__class_weight": [None, "balanced"],
        },
        scoring="f1",
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        n_jobs=-1,
    )
    search.fit(x_train, y_train)
    predictions = search.predict(x_test)

    print(f"Loaded: {source}")
    print(f"Best parameters: {search.best_params_}")
    print(f"Test accuracy: {accuracy_score(y_test, predictions):.3f}")
    print(f"Test F1:      {f1_score(y_test, predictions):.3f}")
    print(classification_report(y_test, predictions, target_names=["No diabetes", "Diabetes"]))

    tree = search.best_estimator_.named_steps["tree"]
    importances = sorted(zip(frame.columns, tree.feature_importances_), key=lambda pair: pair[1], reverse=True)
    print("Feature importance (impurity-based; use with care):")
    for name, importance in importances:
        print(f"  {name:<28} {importance:.3f}")
    print("\nA very deep tree can memorize the training set. Compare train and test scores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
