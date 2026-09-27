# Regularization

## What you will learn

- The difference between underfitting, a useful fit, and overfitting.
- How Ridge's L2 penalty shrinks coefficients.
- How `GridSearchCV` chooses a hyperparameter using cross-validation.
- Why tuning must use training data only.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/regularization/main.py
```

Try changing the alpha grid in `main.py`. A very small alpha behaves like ordinary linear regression. A very large alpha can underfit by making all predictions close to the target mean.

The `Pipeline` is important: each cross-validation fold gets its own preprocessing fit, so no validation-fold statistics leak into the model.
