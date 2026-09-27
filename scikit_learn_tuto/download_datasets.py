#!/usr/bin/env python3
"""Download the Kaggle datasets used by the scikit-learn tutorials.

The script never stores credentials. It expects official Kaggle credentials in
``~/.kaggle/kaggle.json`` or the standard Kaggle environment variables.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from kaggle import api as kaggle_api
except ImportError:
    kaggle_api = None


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_ROOT = ROOT / "data"


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    slug: str
    description: str


DATASETS: dict[str, DatasetSpec] = {
    "telco": DatasetSpec("telco", "blastchar/telco-customer-churn", "Telco Customer Churn (classification)"),
    "medical": DatasetSpec("medical", "mosapabdelghany/medical-insurance-cost-dataset", "Medical Insurance Cost (regression)"),
    "pima": DatasetSpec("pima", "jamaltariqcheema/pima-indians-diabetes-dataset", "Pima Indians Diabetes (classification)"),
    "breast_cancer": DatasetSpec("breast_cancer", "uciml/breast-cancer-wisconsin-data", "Breast Cancer Wisconsin (classification and clustering)"),
    "sms": DatasetSpec("sms", "uciml/sms-spam-collection-dataset", "SMS Spam Collection (text classification)"),
    "credit_card": DatasetSpec("credit_card", "mlg-ulb/creditcardfraud", "Credit Card Fraud (anomaly detection; large download)"),
}


def print_catalog() -> None:
    print("Available Kaggle datasets:\n")
    for spec in DATASETS.values():
        print(f"  {spec.key:<15} {spec.slug}")
        print(f"  {'':<15} {spec.description}\n")


def credentials_available() -> bool:
    if Path.home().joinpath(".kaggle", "kaggle.json").is_file():
        return True
    return bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))


def download_one(spec: DatasetSpec, data_root: Path, force: bool) -> None:
    target = data_root / spec.key
    if target.exists() and any(target.rglob("*")) and not force:
        print(f"{spec.key}: already downloaded at {target} (use --force to redownload)")
        return
    if kaggle_api is None:
        raise RuntimeError(
            "The 'kaggle' package is not installed. Install it with:\n"
            "  uv pip install --python ml_shit/bin/python kaggle"
        )
    if not credentials_available():
        raise RuntimeError(
            "Kaggle credentials were not found. Create ~/.kaggle/kaggle.json "
            "from your Kaggle account settings, then try again."
        )

    target.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {spec.key} from {spec.slug} ...")
    client = kaggle_api.KaggleApi()
    client.dataset_download_files(
        spec.slug,
        path=str(target),
        unzip=True,
        force=force,
        quiet=False,
    )
    print(f"Saved {spec.key} to {target}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), help="Download one dataset key.")
    parser.add_argument("--all", action="store_true", help="Download every catalogued dataset.")
    parser.add_argument("--list", action="store_true", help="Print dataset keys and Kaggle slugs.")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help=f"Destination root (default: {DEFAULT_DATA_ROOT}).",
    )
    parser.add_argument("--force", action="store_true", help="Redownload even if data exists.")
    args = parser.parse_args()
    if not args.list and not args.dataset and not args.all:
        parser.error("choose --dataset KEY, --all, or --list")
    if args.dataset and args.all:
        parser.error("choose only one of --dataset or --all")
    return args


def main() -> int:
    args = parse_args()
    if args.list:
        print_catalog()
        return 0
    keys = sorted(DATASETS) if args.all else [args.dataset]
    data_root = args.data_root.expanduser().resolve()
    for key in keys:
        download_one(DATASETS[key], data_root, args.force)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
