# Scikit-learn Tutorial Series

A progressive, hands-on scikit-learn course. Each topic has its own folder, a short explanation, and a runnable example that uses a real Kaggle dataset. The examples target Python 3.12 and the existing `ml_shit` virtual environment.

## Learning path

| Folder | Topic | Main ideas | Kaggle dataset |
| --- | --- | --- | --- |
| `data_preprocessing` | Missing values, encoding, scaling | `SimpleImputer`, `OneHotEncoder`, `StandardScaler`, `ColumnTransformer` | Telco Customer Churn |
| `train_test_cross_validation` | Splitting and validation | leakage, stratification, `KFold`, `cross_validate` | Telco Customer Churn |
| `linear_regression` | Regression | fitting a line, MAE, RMSE, R² | Medical Insurance |
| `regularization` | Ridge, Lasso, ElasticNet | overfitting, penalties, hyperparameter search | Medical Insurance |
| `logistic_regression` | Classification | probabilities, thresholds, ROC/PR analysis | Telco Customer Churn |
| `decision_trees` | Tree models | splits, depth, pruning, feature importance | Pima Diabetes |
| `random_forest_ensembles` | Ensembles | bagging, random forests, boosting | Pima/Telco |
| `svm_knn` | Distance-based models | scaling, kernels, neighbours, margins | Breast Cancer Wisconsin |
| `clustering` | Unsupervised learning | K-Means, cluster validation, silhouettes | Breast Cancer Wisconsin |
| `dimensionality_reduction` | Feature compression | scaling, PCA, explained variance | Breast Cancer Wisconsin |
| `text_classification` | Text features | TF-IDF, n-grams, sparse matrices | SMS Spam Collection |
| `pipelines` | Reliable workflows | pipelines, tuning, persistence | Telco Customer Churn |
| `imbalanced_classification` | Unequal classes | class weights, balanced metrics, PR curves | Telco Customer Churn |
| `anomaly_detection` | Outliers | Isolation Forest, contamination, false positives | Credit Card Fraud |

The folders build on one another. Start with `data_preprocessing`, then `train_test_cross_validation`, and continue in order.

## Kaggle setup

Kaggle downloads require your own Kaggle account and API token. **Never put `kaggle.json` in this repository.** Put it at `~/.kaggle/kaggle.json`, then install the downloader dependency into the existing environment:

```bash
cd /home/nishant/Nishant_stuff
uv pip install --python ml_shit/bin/python kaggle
```

List the catalogued datasets:

```bash
ml_shit/bin/python scikit_learn_tuto/download_datasets.py --list
```

Download one dataset:

```bash
ml_shit/bin/python scikit_learn_tuto/download_datasets.py --dataset telco
```

Download all teaching datasets (the credit-card file is large):

```bash
ml_shit/bin/python scikit_learn_tuto/download_datasets.py --all
```

Files are placed in `scikit_learn_tuto/data/<topic>/`. Raw Kaggle files are ignored by git because they can be large and have their own licenses. Examples search recursively for a CSV and accept `--data PATH` when the downloaded file name differs.

## Run an example

From the repository root:

```bash
ml_shit/bin/python scikit_learn_tuto/data_preprocessing/main.py
ml_shit/bin/python scikit_learn_tuto/linear_regression/main.py
ml_shit/bin/python scikit_learn_tuto/logistic_regression/main.py --data path/to/your.csv
```

Read the markdown file beside `main.py` first, then change one hyperparameter and observe the result. Experimentation is the important part of the lesson.

## Dataset catalogue

| Key | Kaggle page | Used for |
| --- | --- | --- |
| `telco` | [blastchar/telco-customer-churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) | preprocessing, classification, pipelines, imbalance |
| `medical` | [mosapabdelghany/medical-insurance-cost-dataset](https://www.kaggle.com/datasets/mosapabdelghany/medical-insurance-cost-dataset) | regression and regularization |
| `pima` | [jamaltariqcheema/pima-indians-diabetes-dataset](https://www.kaggle.com/datasets/jamaltariqcheema/pima-indians-diabetes-dataset) | trees and ensembles |
| `breast_cancer` | [uciml/breast-cancer-wisconsin-data](https://www.kaggle.com/datasets/uciml/breast-cancer-wisconsin-data) | SVM, k-NN, clustering, and PCA |
| `sms` | [uciml/sms-spam-collection-dataset](https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset) | text vectorization and classification |
| `credit_card` | [mlg-ulb/creditcardfraud](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) | anomaly detection |

These are educational baselines, not medical, financial, or production-ready models. Inspect the data, split before fitting preprocessing, choose metrics that match the real cost of mistakes, and treat cross-validation as an estimate rather than a guarantee.
