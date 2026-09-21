"""Local files: read, save, look around, find, move.

All paths are absolute -- the model gets burned by relative paths, so every
docstring says so and inspect_path prints the cwd in every answer as a hint.
Writes never lose data silently: overwrite keeps a timestamped backup,
transfer refuses to clobber an existing file.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from ._common import _truncate


def read_file(path: str) -> str:
    """Return the text contents of a file.

    Args:
        path: Absolute path of the file to read.
    """
    with open(path, encoding="utf-8") as f:
        return _truncate(f.read())


def save_file(path: str, content: str, mode: str = "overwrite") -> str:
    """Write `content` to `path`, creating missing parent folders as needed.

    One tool covers both cases: overwrite replaces the file (the old version
    is copied to `<name>.bak-<timestamp>` first, and restored if the write
    itself fails), append adds to the end for logs and notes that must not
    be erased.

    Args:
        path: Absolute path of the file to write.
        content: Full text to write or append.
        mode: "overwrite" to replace, "append" to add to the end.
    """
    if mode not in ("overwrite", "append"):
        raise ValueError(f"mode must be 'overwrite' or 'append', got '{mode}'")
    dest = Path(path)
    if dest.parent and not dest.parent.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append":
        existed = dest.is_file()
        with open(dest, "a", encoding="utf-8") as f:
            f.write(content)
        action = "appended to" if existed else "created and wrote to"
        return f"{action} {path} ({len(content)} characters added)"
    if dest.is_file():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = dest.with_name(f"{dest.name}.bak-{timestamp}")
        counter = 1
        while backup.exists():
            counter += 1
            backup = dest.with_name(f"{dest.name}.bak-{timestamp}-{counter}")
        shutil.copy2(dest, backup)
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            shutil.copy2(backup, dest)
            raise
        return (
            f"wrote {len(content)} characters to {path} "
            f"(original backed up to {backup})"
        )
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {len(content)} characters to {path}"


def inspect_path(path: str = "") -> str:
    """Say what a path is and show directory contents.

    Three tools folded into one: empty path means "here" (prints the cwd and
    lists it), a directory lists its entries with trailing slashes, a file
    reports size and mtime. Call before reading, writing, or moving anything.

    Args:
        path: Absolute path to inspect; empty means the current directory.
    """
    target = Path(path) if path else Path(os.getcwd())
    if not target.exists():
        return f"{target} does not exist (current directory: {os.getcwd()})"
    if target.is_file():
        stat = target.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"{target}: file, {stat.st_size} bytes, modified {modified}"
    entries = sorted(target.iterdir())
    if not entries:
        return f"{target} is empty (current directory: {os.getcwd()})"
    listing = "\n".join(f"{e.name}/" if e.is_dir() else e.name for e in entries)
    return _truncate(f"{target} (current directory: {os.getcwd()})\n{listing}")


def search_files(directory: str, pattern: str) -> str:
    """Find files by name below a directory, recursive glob, newest tool.

    Args:
        directory: Absolute path of the directory to search in.
        pattern: Glob like "*.py" or "config*".
    """
    matches = sorted(str(p) for p in Path(directory).rglob(pattern) if p.is_file())
    if not matches:
        return f"no files matching '{pattern}' under {directory}"
    listing = "\n".join(matches[:50])
    if len(matches) > 50:
        listing += f"\n... and {len(matches) - 50} more"
    return _truncate(listing)


def transfer_file(source: str, destination: str, action: str = "copy") -> str:
    """Copy or move a file or directory. Never overwrites an existing file.

    Args:
        source: Absolute path to copy or move.
        destination: Absolute path to copy or move it to.
        action: "copy" to duplicate, "move" to rename/relocate.
    """
    if action not in ("copy", "move"):
        raise ValueError(f"action must be 'copy' or 'move', got '{action}'")
    if Path(destination).is_file():
        raise FileExistsError(
            f"destination already exists: {destination} -- pick another path"
        )
    parent = Path(destination).parent
    if str(parent) and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    if action == "copy":
        if Path(source).is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return f"copied {source} to {destination}"
    shutil.move(source, destination)
    return f"moved {source} to {destination}"
