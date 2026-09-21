"""Filesystem tools: read, save, inspect, find, and move files."""

import os
import shutil
from datetime import datetime
from pathlib import Path

from ._common import _truncate, tool


@tool
def read_file(path: str) -> str:
    """Read and return the text contents of a file.

    Use this whenever you need to see what is inside a file.

    Args:
        path: Absolute path of the file to read.
    """
    with open(path, encoding="utf-8") as f:
        return _truncate(f.read())


@tool
def save_file(path: str, content: str, mode: str = "overwrite") -> str:
    """Create or update a file with the given text content.

    Use this when the user asks you to save text, notes, or code to a file.
    mode="overwrite" replaces the file (the original is backed up first,
    restored if the write fails). mode="append" grows logs/notes without
    erasing -- anything where overwriting would destroy what is there.
    Missing parent directories are created automatically.

    Args:
        path: Absolute path of the file to write.
        content: The complete text content for the file.
        mode: "overwrite" to replace the file, "append" to add to the end.
    """
    dest = Path(path)
    if mode not in ("overwrite", "append"):
        raise ValueError(f"mode must be 'overwrite' or 'append', got '{mode}'")
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
        backup_path = dest.with_name(f"{dest.name}.bak-{timestamp}")
        counter = 1
        while backup_path.exists():
            counter += 1
            backup_path = dest.with_name(f"{dest.name}.bak-{timestamp}-{counter}")
        shutil.copy2(dest, backup_path)
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            # Restore the original so a failed write never loses data.
            shutil.copy2(backup_path, dest)
            raise
        return (
            f"wrote {len(content)} characters to {path} "
            f"(original backed up to {backup_path})"
        )
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {len(content)} characters to {path}"


@tool
def inspect_path(path: str = "") -> str:
    """Inspect a file or directory: existence, type, size, and contents.

    No arguments (or empty string) reports the current working directory and
    lists it -- use this when the user says "here" or "this folder". A
    directory path lists its entries (files plain, subdirectories with a
    trailing slash). A file path reports size and modification time. Call
    this before reading, writing, or moving anything.

    Args:
        path: Absolute path to inspect. Empty means the current directory.
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


@tool
def search_files(directory: str, pattern: str) -> str:
    """Find files whose name matches a glob pattern, searching recursively.

    Use this to locate files when you do not know their exact path.

    Args:
        directory: Absolute path of the directory to search in.
        pattern: Glob pattern for file names, for example "*.py" or "config*".
    """
    matches = sorted(
        str(p) for p in Path(directory).rglob(pattern) if p.is_file()
    )
    if not matches:
        return f"no files matching '{pattern}' under {directory}"
    listing = "\n".join(matches[:50])
    if len(matches) > 50:
        listing += f"\n... and {len(matches) - 50} more"
    return _truncate(listing)


@tool
def transfer_file(source: str, destination: str, action: str = "copy") -> str:
    """Copy or move a file or directory to a new location.

    Refuses to overwrite an existing file; copying/moving into an existing
    directory is allowed. Missing parent directories are created.

    Args:
        source: Absolute path of the file or directory to copy or move.
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
