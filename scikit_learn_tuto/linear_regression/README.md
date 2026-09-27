# Linear regression

## What you will learn

- The regression workflow: features, target, split, fit, predict, evaluate.
- Why one-hot encoding is needed for categorical columns.
- The difference between MAE, RMSE, and R².
- How to package preprocessing and a model in a `Pipeline`.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/linear_regression/main.py
```

The medical-insurance target is `charges`, a continuous value. The model learns one coefficient per transformed feature. Coefficients are useful for direction and rough importance, but they are not causal effects.

## Metrics

- **MAE** is the average number of currency units the prediction is off.
- **RMSE** grows more quickly when a few predictions are very wrong.
- **R²** compares the model with predicting the training mean; it is not a percentage accuracy and can be negative on a poor test set.
