# Anomaly detection

## What you will learn

- The difference between supervised fraud detection and unsupervised anomaly detection.
- How Isolation Forest isolates rare points with random trees.
- What `contamination="auto"` means and why it is a modelling assumption.
- How to evaluate anomalies when known labels are available for research.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/anomaly_detection/main.py --sample 20000
```

The Kaggle credit-card dataset is large, so this example takes a reproducible sample by default. In a real system, do not assume every statistical anomaly is fraud and do not deploy a detector without a review and feedback loop.
