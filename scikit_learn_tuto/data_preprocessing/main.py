"""Lesson 1: turn messy Telco data into numeric model features."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from tutorial_utils import add_data_argument, load_telco


def build_preprocessor(features):
    numeric = features.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    numeric_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, numeric),
            ("categorical", categorical_pipeline, categorical),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "telco")
    args = parser.parse_args()

    frame, source = load_telco(args.data)
    features = frame.drop(columns=["Churn", "customerID"], errors="ignore")
    target = frame["Churn"]
    x_train, x_test, _, _ = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )

    print(f"Loaded: {source}")
    print(f"Rows before split: {len(frame):,}")
    print(f"Train/test rows: {len(x_train):,}/{len(x_test):,}")
    print(f"Missing values before preprocessing: {int(features.isna().sum().sum()):,}")

    preprocessor = build_preprocessor(features)
    train_processed = preprocessor.fit_transform(x_train)
    test_processed = preprocessor.transform(x_test)
    print("Missing values after imputation: 0")
    print(f"Transformed train shape: {train_processed.shape}")
    print(f"Transformed test shape:  {test_processed.shape}")
    print("fit_transform was used on train only; test used transform to prevent leakage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
