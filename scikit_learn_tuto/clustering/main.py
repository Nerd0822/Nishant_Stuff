"""Lesson 9: discover patient groups with K-Means clustering."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tutorial_utils import add_data_argument, load_breast_cancer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "breast_cancer")
    args = parser.parse_args()

    features, _, source = load_breast_cancer(args.data)
    scaled = StandardScaler().fit_transform(features)
    print(f"Loaded: {source}")
    print("K-Means is unsupervised: the class labels are not used to create clusters.")
    print("k  silhouette  cluster sizes")
    results = []
    for cluster_count in range(2, 9):
        labels = KMeans(n_clusters=cluster_count, n_init=10, random_state=42).fit_predict(scaled)
        score = silhouette_score(scaled, labels)
        sizes = pd.Series(labels).value_counts().sort_index().tolist()
        results.append((cluster_count, score, sizes))
        print(f"{cluster_count}  {score:>10.3f}  {sizes}")

    best_k, best_score, _ = max(results, key=lambda result: result[1])
    final_labels = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit_predict(scaled)
    print(f"\nHighest silhouette score: k={best_k} ({best_score:.3f})")
    two_dimensions = PCA(n_components=2).fit_transform(scaled)
    print("PCA coordinates are for visualization; clusters were fitted in full space.")
    print(f"First ten 2-D coordinates: {two_dimensions[:10].round(2).tolist()}")
    print(f"First ten cluster labels:   {final_labels[:10].tolist()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
