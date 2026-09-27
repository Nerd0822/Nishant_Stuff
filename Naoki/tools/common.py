import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _resolve(path: str) -> Path:
    p = (ROOT / path).resolve() if not os.path.isabs(path) else Path(path).resolve()
    return p
