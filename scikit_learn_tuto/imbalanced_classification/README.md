# Imbalanced classification

## What you will learn

- Why accuracy can look good while missing almost every rare positive case.
- How `class_weight="balanced"` changes training.
- How balanced accuracy, ROC AUC, and average precision answer different questions.
- Why resampling and threshold selection require care.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/imbalanced_classification/main.py
```

Always keep the test distribution untouched. Compare models with metrics that match the application, and report the confusion matrix rather than one headline number.
