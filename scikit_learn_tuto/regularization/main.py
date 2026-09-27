"""Lesson 4: compare ordinary regression with Ridge regularization."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from tutorial_utils import add_data_argument, load_medical


def make_preprocessor(features):
    numeric = features.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    return ColumnTransformer(
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


def score_model(name, model, x_test, y_test):
    predictions = model.predict(x_test)
    print(
        f"{name:<18} MAE={mean_absolute_error(y_test, predictions):,.2f} "
        f"RMSE={mean_squared_error(y_test, predictions) ** 0.5:,.2f} "
        f"R2={r2_score(y_test, predictions):.3f}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "medical")
    args = parser.parse_args()

    frame, source = load_medical(args.data)
    target = frame.pop("charges")
    x_train, x_test, y_train, y_test = train_test_split(
        frame, target, test_size=0.2, random_state=42
    )
    preprocessor = make_preprocessor(frame)
    ordinary = Pipeline([("preprocessor", clone(preprocessor)), ("regressor", LinearRegression())])
    ridge = Pipeline([("preprocessor", clone(preprocessor)), ("regressor", Ridge(max_iter=10_000))])
    search = GridSearchCV(
        ridge,
        param_grid={"regressor__alpha": np.logspace(-3, 3, 13)},
        scoring="neg_mean_absolute_error",
        cv=KFold(n_splits=5, shuffle=True, random_state=42),
        n_jobs=-1,
    )
    ordinary.fit(x_train, y_train)
    search.fit(x_train, y_train)

    print(f"Loaded: {source}")
    print("Medical charges: ordinary regression versus tuned Ridge")
    score_model("LinearRegression", ordinary, x_test, y_test)
    score_model("Ridge", search.best_estimator_, x_test, y_test)
    print(f"Best alpha: {search.best_params_['regressor__alpha']:.4g}")
    print("Ridge shrinks coefficients toward zero, which can improve generalization.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
