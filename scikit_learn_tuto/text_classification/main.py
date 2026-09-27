"""Lesson 11: turn SMS text into TF-IDF features and classify spam."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from tutorial_utils import add_data_argument, load_sms


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_data_argument(parser, "sms")
    args = parser.parse_args()

    messages, target, source = load_sms(args.data)
    x_train, x_test, y_train, y_test = train_test_split(
        messages, target, test_size=0.2, random_state=42, stratify=target
    )
    model = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                ),
            ),
            ("classifier", LogisticRegression(max_iter=2_000, class_weight="balanced", random_state=42)),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    print(f"Loaded: {source}")
    print(f"Training messages: {len(x_train):,}; test messages: {len(x_test):,}")
    print(f"Vocabulary size: {len(model.named_steps['tfidf'].vocabulary_):,}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
    print(f"F1:      {f1_score(y_test, predictions):.3f}")
    print(classification_report(y_test, predictions, target_names=["Ham", "Spam"]))
    print("A bag-of-words model ignores word order; n-grams add a little local context.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
