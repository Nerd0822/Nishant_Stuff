# Data preprocessing

## What you will learn

- Why raw datasets contain missing values and mixed data types.
- How to split data before learning preprocessing statistics.
- The difference between numeric and categorical features.
- How `SimpleImputer`, `OneHotEncoder`, `StandardScaler`, and `ColumnTransformer` work together.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/data_preprocessing/main.py
```

Use `--data path/to/WA_Fn-UseC_-Telco-Customer-Churn.csv` if the Kaggle file is outside `scikit_learn_tuto/data/telco`.

## Key idea

Never fit a scaler or imputer on the test set. `fit_transform(X_train)` learns statistics from training data, while `transform(X_test)` only applies already learned statistics. This prevents information from the test set leaking into training.

The target (`Churn`) is kept separate from the feature matrix. `customerID` is an identifier, not a useful predictive feature, so it is removed.
