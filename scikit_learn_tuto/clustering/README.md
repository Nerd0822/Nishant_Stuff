# Clustering

## What you will learn

- The difference between supervised and unsupervised learning.
- How K-Means assigns points to centroids.
- What a silhouette score measures.
- Why scaling and choosing `k` matter.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/clustering/main.py
```

K-Means assumes roughly round clusters and is sensitive to scaling and initial centroid positions. A higher silhouette score is not automatically a useful business segmentation; inspect cluster descriptions before acting. The known diagnosis column is not used to fit the clusters.
