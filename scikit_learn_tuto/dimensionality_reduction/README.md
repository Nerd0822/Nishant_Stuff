# Dimensionality reduction

## What you will learn

- What a principal component is.
- How explained variance tells you how much information a component retains.
- How PCA can remove redundant dimensions before a model.
- The difference between compression and feature selection.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/dimensionality_reduction/main.py
```

PCA is fitted on training data only. The test set uses the same mean, scale, and component directions learned from training. Fewer components can be faster or more stable, but a lower-dimensional representation is not always better for the final task.
