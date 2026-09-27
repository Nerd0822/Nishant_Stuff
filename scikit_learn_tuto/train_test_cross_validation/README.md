# Train/test splitting and cross-validation

## What you will learn

- Why a model must be evaluated on data it did not train on.
- What data leakage means.
- Why stratification is useful for classification targets.
- How `StratifiedKFold` and `cross_validate` estimate performance more reliably than one lucky split.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/train_test_cross_validation/main.py
```

A single test score is only one estimate and can change with `random_state`. Five-fold cross-validation trains five different models and reports the mean and spread. Accuracy is useful when classes are reasonably balanced; ROC AUC and F1 are often more informative for churn because the positive class is less common.

The entire preprocessing pipeline is inside the estimator passed to cross-validation. Each fold therefore learns its own imputations, scaling parameters, and one-hot vocabulary.
