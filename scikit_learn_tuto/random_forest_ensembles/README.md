# Random forests and ensembles

## What you will learn

- Why one decision tree can be unstable.
- The bagging idea behind a random forest.
- The boosting idea behind gradient boosting.
- Why class weights can help when the positive class is smaller.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/random_forest_ensembles/main.py
```

A random forest reduces variance by averaging many trees. Gradient boosting builds trees sequentially and focuses on errors made by earlier trees. Neither technique automatically fixes bad features, leakage, or an unsuitable metric.
