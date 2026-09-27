# Text classification

## What you will learn

- Why raw text cannot be passed directly to most scikit-learn estimators.
- What TF-IDF weights and why rare words can be informative.
- What unigrams and bigrams mean.
- How a text vectorizer belongs inside a reproducible pipeline.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/text_classification/main.py
```

The vectorizer learns its vocabulary from the training messages only. Calling `fit` on all messages before splitting would leak information from the test set. This example is a strong baseline, not a deep-learning language model.
