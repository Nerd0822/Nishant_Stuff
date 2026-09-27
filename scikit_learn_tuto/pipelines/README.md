# Pipelines and persistence

## What you will learn

- Why a pipeline is safer than manually applying preprocessing steps.
- How `GridSearchCV` tunes a parameter inside a pipeline.
- How to save and reload a fitted estimator with `joblib`.
- What must be included when saving a model for later inference.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/pipelines/main.py --save artifacts/telco_pipeline.joblib
```

The saved object contains the imputer, encoder, scaler, and classifier together. That makes preprocessing at prediction time much less error-prone. Treat a saved model as a versioned software artifact: record the training data, library versions, and evaluation results alongside it.
