"""Lesson 10: compress features with principal component analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from tutorial_utils import add_data_argument, load_breast_cancer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "breast_cancer")
    args = parser.parse_args()

    features, target, source = load_breast_cancer(args.data)
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    train_scaled = StandardScaler().fit_transform(x_train)
    pca_full = PCA().fit(train_scaled)
    cumulative = pca_full.explained_variance_ratio_.cumsum()
    print(f"Loaded: {source}")
    print("Components needed to retain a percentage of variance:")
    for threshold in (0.90, 0.95, 0.99):
        count = int((cumulative < threshold).sum() + 1)
        print(f"  {threshold:.0%}: {count}")

    models = {
        "Original features": Pipeline([("scale", StandardScaler()), ("classifier", LogisticRegression(max_iter=2_000))]),
        "PCA (95% variance)": Pipeline(
            [
                ("scale", StandardScaler()),
                ("pca", PCA(n_components=0.95, svd_solver="full")),
                ("classifier", LogisticRegression(max_iter=2_000)),
            ]
        ),
    }
    for name, model in models.items():
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        print(
            f"{name:<22} accuracy={accuracy_score(y_test, predictions):.3f} "
            f"roc_auc={roc_auc_score(y_test, probabilities):.3f}"
        )
    print("PCA creates linear combinations of features; it does not create new information.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
