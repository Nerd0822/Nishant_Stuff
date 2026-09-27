# Logistic regression

## What you will learn

- Why logistic regression predicts probabilities for binary classes.
- How the default `0.5` decision threshold works.
- How to read a confusion matrix and classification report.
- Why ROC AUC and average precision should be considered together when classes are imbalanced.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/logistic_regression/main.py
```

`predict_proba` returns a probability for each class. A threshold does not change the ranking of customers; it changes which customers are acted on. Experiment with thresholds and connect the choice to a real business cost.
