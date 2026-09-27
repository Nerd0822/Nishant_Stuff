"""Small helpers shared by the scikit-learn tutorial scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "data"


def find_data_file(
    topic: str,
    explicit_path: str | Path | None = None,
    extensions: Iterable[str] = (".csv",),
) -> Path:
    """Find a dataset file for a tutorial.

    ``explicit_path`` may point to a file or directory. If omitted, files are
    searched recursively under ``data/<topic>``.
    """
    extensions = tuple(extensions)
    if explicit_path is not None:
        candidate = Path(explicit_path).expanduser().resolve()
        if candidate.is_file():
            return candidate
        if candidate.is_dir():
            files = sorted(
                path
                for path in candidate.rglob("*")
                if path.is_file() and path.suffix.lower() in extensions
            )
            if files:
                return files[0]
        raise FileNotFoundError(f"No supported data file found at: {candidate}")

    topic_root = DATA_ROOT / topic
    if not topic_root.exists():
        raise FileNotFoundError(
            f"Dataset folder does not exist: {topic_root}\n"
            "Run download_datasets.py or pass --data PATH."
        )

    files = sorted(
        path
        for path in topic_root.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions
    )
    if not files:
        raise FileNotFoundError(
            f"No data file found under: {topic_root}\n"
            "Download the dataset or pass --data PATH."
        )
    return files[0]


def load_dataframe(
    topic: str,
    explicit_path: str | Path | None = None,
    extensions: Iterable[str] = (".csv",),
) -> tuple[pd.DataFrame, Path]:
    """Load a tutorial CSV and return both the frame and its source path."""
    path = find_data_file(topic, explicit_path, extensions)
    return pd.read_csv(path), path


def add_data_argument(parser, topic: str) -> None:
    """Add the common ``--data`` option to an argparse parser."""
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help=(
            f"Path to a CSV for the {topic} lesson. If omitted, "
            f"scikit_learn_tuto/data/{topic} is searched."
        ),
    )


def require_columns(frame: pd.DataFrame, columns: Iterable[str], context: str) -> None:
    """Raise a useful error when a downloaded Kaggle file has a different shape."""
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        available = ", ".join(map(str, frame.columns))
        raise ValueError(
            f"{context} is missing expected column(s): {missing}.\n"
            f"Available columns: {available}"
        )


def load_telco(explicit_path: str | Path | None = None) -> tuple[pd.DataFrame, Path]:
    """Load and normalize the common Telco churn CSV."""
    frame, source = load_dataframe("telco", explicit_path)
    require_columns(frame, ["Churn"], "Telco dataset")
    frame = frame.copy()
    if "TotalCharges" in frame.columns:
        frame["TotalCharges"] = pd.to_numeric(frame["TotalCharges"], errors="coerce")
    target = frame["Churn"].astype(str).str.strip().str.lower().map({"no": 0, "yes": 1})
    if target.isna().any():
        raise ValueError("Telco Churn must contain only 'Yes' or 'No' values.")
    frame["Churn"] = target.astype(int)
    return frame, source


def load_medical(explicit_path: str | Path | None = None) -> tuple[pd.DataFrame, Path]:
    """Load and normalize the medical-insurance regression CSV."""
    frame, source = load_dataframe("medical", explicit_path)
    require_columns(frame, ["charges"], "Medical-insurance dataset")
    frame = frame.copy()
    frame["charges"] = pd.to_numeric(frame["charges"], errors="coerce")
    if frame["charges"].isna().any():
        raise ValueError("The medical-insurance target contains non-numeric values.")
    return frame, source


def load_breast_cancer(
    explicit_path: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.Series, Path]:
    """Load the Kaggle Breast Cancer Wisconsin CSV and return X, y, source."""
    frame, source = load_dataframe("breast_cancer", explicit_path)
    frame = frame.loc[:, ~frame.columns.astype(str).str.lower().str.startswith("unnamed")]
    target_name = next(
        (
            column
            for column in ("diagnosis", "target", "class", "label")
            if column in frame.columns
        ),
        None,
    )
    if target_name is None:
        raise ValueError(
            "Could not find a breast-cancer target column. Expected one of: "
            "diagnosis, target, class, label."
        )

    target = frame[target_name].astype(str).str.strip().str.lower().map(
        {"m": 1, "malignant": 1, "b": 0, "benign": 0}
    )
    if target.isna().any():
        target = pd.to_numeric(frame[target_name], errors="coerce")
    if target.isna().any():
        raise ValueError("The breast-cancer target could not be converted to 0/1 labels.")

    features = frame.drop(columns=[target_name])
    features = features.drop(
        columns=[
            column
            for column in features.columns
            if column.lower() in {"id", "unnamed: 32", "unnamed: 0"}
        ],
        errors="ignore",
    )
    for column in features.columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")
    return features, target.astype(int), source


def load_sms(explicit_path: str | Path | None = None) -> tuple[pd.Series, pd.Series, Path]:
    """Load the Kaggle SMS Spam Collection CSV and return text, labels, source."""
    frame, source = load_dataframe("sms", explicit_path)
    label_name = next(
        (column for column in ("v1", "label", "target", "class") if column in frame.columns),
        None,
    )
    text_name = next(
        (column for column in ("v2", "message", "text") if column in frame.columns),
        None,
    )
    if label_name is None or text_name is None:
        raise ValueError(
            "Could not identify SMS columns. Expected labels named v1/label/target "
            "and text named v2/message/text."
        )
    labels = frame[label_name].astype(str).str.strip().str.lower().map({"ham": 0, "spam": 1})
    if labels.isna().any():
        labels = pd.to_numeric(frame[label_name], errors="coerce")
    if labels.isna().any():
        raise ValueError("SMS labels must be ham/spam or numeric 0/1 values.")
    return frame[text_name].fillna("").astype(str), labels.astype(int), source
