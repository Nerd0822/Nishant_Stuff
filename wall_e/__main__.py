"""Entry point: `python -m wall_e` or `python wall_e/__main__.py`."""

import sys
from pathlib import Path

# Allow running directly: `python wall_e/__main__.py` from inside the package,
# or `python -m wall_e` from the parent directory.
if __package__ is None or __package__ == "":
    _pkg_parent = str(Path(__file__).resolve().parent.parent)
    if _pkg_parent not in sys.path:
        sys.path.insert(0, _pkg_parent)
    from wall_e.cli import main
else:
    from .cli import main

main()