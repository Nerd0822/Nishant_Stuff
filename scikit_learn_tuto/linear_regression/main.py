"""Lesson 3: predict medical charges with linear regression."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from tutorial_utils import add_data_argument, load_medical


def make_model(features):
    numeric = features.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    preprocessor = ColumnTransformer(
        [
            ("numeric", SimpleImputer(strategy="median"), numeric),
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
    return Pipeline([("preprocessor", preprocessor), ("regressor", LinearRegression())])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "medical")
    args = parser.parse_args()

    frame, source = load_medical(args.data)
    target = frame.pop("charges")
    x_train, x_test, y_train, y_test = train_test_split(
        frame, target, test_size=0.2, random_state=42
    )
    model = make_model(frame)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    print(f"Loaded: {source}")
    print(f"Train rows: {len(x_train):,}; test rows: {len(x_test):,}")
    print(f"MAE  (average absolute error): {mean_absolute_error(y_test, predictions):,.2f}")
    print(f"RMSE (penalizes large errors): {mean_squared_error(y_test, predictions) ** 0.5:,.2f}")
    print(f"R^2  (variance explained):       {r2_score(y_test, predictions):.3f}")
    print("\nMAE is usually the easiest regression metric to explain to a stakeholder.")
    print("Try changing the test size and random_state to see how much the score moves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
