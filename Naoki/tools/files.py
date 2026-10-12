"""File tools for Naoki.

Nothing here catches exceptions on purpose. If a file is missing, is a
directory, or is not writable, the real OSError propagates so the agent sees
the actual error instead of a paraphrase of it. The one thing guarded is the
ordering: write_file and delete_file back up before they touch anything, and a
failed backup aborts the operation rather than risking the only copy.
"""

import shutil
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool

from config import BACKUP_DIR


def _stamp() -> str:
    """Sortable timestamp, microseconds included so backups never collide."""
    return datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")


def backup_file(path: Path) -> str:
    """Copy path into BACKUP_DIR as <name>.<timestamp>.bak and return the copy.

    Raises OSError if the copy fails, which callers use to abort. Returns
    "(nothing to back up)" if the source is missing, which is the normal case
    when write_file creates a brand new file.
    """
    if not path.is_file():
        return "(nothing to back up)"

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / f"{path.name}.{_stamp()}.bak"
    shutil.copy2(path, dest)  # copy2 keeps mtime, so backups show the original date
    return str(dest)


@tool
def read_file(path: str) -> str:
    """Read a text file and return its contents. Args: path."""
    return Path(path).read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Overwrite a text file, backing up the original first. Args: path, content."""
    p = Path(path)
    saved = backup_file(p)  # raises on failure, so a bad backup means no write
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {len(content)} chars to {p} (backup: {saved})"


@tool
def create_file(path: str, content: str = "") -> str:
    """Create a new text file. Raises FileExistsError if it is already there. Args: path, content."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x", encoding="utf-8") as f:  # "x" raises FileExistsError itself
        f.write(content)
    return f"created {p} ({len(content)} chars)"


@tool
def delete_file(path: str) -> str:
    """Delete a file after backing it up. Args: path."""
    p = Path(path)
    saved = backup_file(p)  # raises on failure, so a bad backup means no delete
    p.unlink()
    return f"deleted {p} (backup: {saved})"