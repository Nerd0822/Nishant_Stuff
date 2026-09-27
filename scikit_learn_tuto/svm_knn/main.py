"""Lesson 8: compare distance-based SVM and k-nearest-neighbour models."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from tutorial_utils import add_data_argument, load_breast_cancer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "breast_cancer")
    args = parser.parse_args()

    features, target, source = load_breast_cancer(args.data)
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    models = {
        "RBF SVM": SVC(C=1.0, gamma="scale", probability=True, random_state=42),
        "KNN (k=10)": KNeighborsClassifier(n_neighbors=10),
    }
    print(f"Loaded: {source}")
    print(f"Train/test rows: {len(x_train)}/{len(x_test)}")
    for name, estimator in models.items():
        model = Pipeline([("scale", StandardScaler()), ("classifier", estimator)])
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, 1]
        print(f"\n{name}")
        print(f"  accuracy: {accuracy_score(y_test, predictions):.3f}")
        print(f"  ROC AUC:  {roc_auc_score(y_test, probabilities):.3f}")
        print(classification_report(y_test, predictions, target_names=["Benign", "Malignant"]))
    print("Both models use distances, so scaling is part of the model—not optional cleanup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
