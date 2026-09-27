# SVM and k-nearest neighbours

## What you will learn

- How k-NN makes a prediction from nearby training examples.
- How an SVM creates a margin between classes.
- Why feature scaling is essential for distance- and margin-based models.
- How to compare models fairly on the same split.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/svm_knn/main.py
```

The scaler is inside the pipeline, so it is fitted only on each training fold. Try changing `C` for the SVM or `n_neighbors` for k-NN and observe the trade-off between model complexity and generalization.
