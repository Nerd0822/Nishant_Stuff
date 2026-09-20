"""File tools: reading, writing, finding, and organizing files."""

import os
import shutil
from datetime import datetime
from pathlib import Path

from ._common import _truncate


def read_file(file_path: str) -> str:
    """Read and return the text contents of a file.

    Use this whenever you need to see what is inside a file.

    Args:
        file_path: Absolute path of the file to read.
    """
    with open(file_path, encoding="utf-8") as f:
        return _truncate(f.read())


def write_file(file_path: str, content: str) -> str:
    """Create or overwrite a file with the given text content.

    Use this when the user asks you to save text, notes, or code to a file.
    If the file already exists, the original is backed up before overwriting.

    Args:
        file_path: Absolute path of the file to write.
        content: The complete text content for the file.
    """
    path = Path(file_path)
    if path.is_file():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{timestamp}")
        counter = 1
        while backup_path.exists():
            counter += 1
            backup_path = path.with_name(f"{path.name}.bak-{timestamp}-{counter}")
        shutil.copy2(path, backup_path)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            # Restore the original so a failed write never loses data.
            shutil.copy2(backup_path, path)
            raise
        return (
            f"wrote {len(content)} characters to {file_path} "
            f"(original backed up to {backup_path})"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {len(content)} characters to {file_path}"


def list_directory(directory_path: str) -> str:
    """List the files and subdirectories inside a directory.

    Use this to explore a folder before reading, writing, or running commands.

    Args:
        directory_path: Absolute path of the directory to list.
    """
    entries = sorted(Path(directory_path).iterdir())
    if not entries:
        return f"{directory_path} is empty"
    listing = "\n".join(f"{e.name}/" if e.is_dir() else e.name for e in entries)
    return _truncate(listing)


def find_files(directory_path: str, pattern: str) -> str:
    """Find files whose name matches a glob pattern, searching recursively.

    Use this to locate files when you do not know their exact path.

    Args:
        directory_path: Absolute path of the directory to search in.
        pattern: Glob pattern for file names, for example "*.py" or "config*".
    """
    matches = sorted(
        str(path) for path in Path(directory_path).rglob(pattern) if path.is_file()
    )
    if not matches:
        return f"no files matching '{pattern}' under {directory_path}"
    listing = "\n".join(matches[:50])
    if len(matches) > 50:
        listing += f"\n... and {len(matches) - 50} more"
    return _truncate(listing)


def file_info(file_path: str) -> str:
    """Report whether a path exists and, if so, its type, size and modification time.

    Use this to check a file or folder before reading, writing, or moving it.

    Args:
        file_path: Absolute path of the file or directory to inspect.
    """
    path = Path(file_path)
    if not path.exists():
        return f"{file_path} does not exist"
    kind = "directory" if path.is_dir() else "file"
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    return f"{file_path}: {kind}, {stat.st_size} bytes, modified {modified}"


def copy_file(source: str, destination: str) -> str:
    """Copy a file or directory to a new location.

    Refuses to overwrite an existing file; copy into an existing directory is allowed.

    Args:
        source: Absolute path of the file or directory to copy.
        destination: Absolute path to copy it to.
    """
    if Path(destination).is_file():
        raise FileExistsError(
            f"destination already exists: {destination} -- pick another path"
        )
    if Path(source).is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)
    return f"copied {source} to {destination}"


def move_file(source: str, destination: str) -> str:
    """Move or rename a file or directory.

    Refuses to overwrite an existing file; moving into an existing directory is allowed.

    Args:
        source: Absolute path of the file or directory to move.
        destination: Absolute path to move it to.
    """
    if Path(destination).is_file():
        raise FileExistsError(
            f"destination already exists: {destination} -- pick another path"
        )
    shutil.move(source, destination)
    return f"moved {source} to {destination}"


def make_directory(directory_path: str) -> str:
    """Create a directory, including any missing parent directories.

    Args:
        directory_path: Absolute path of the directory to create.
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)
    return f"directory ready: {directory_path}"


def current_directory() -> str:
    """Report the assistant's current working directory.

    No arguments. Use this when the user says 'here' or 'this folder', or
    you need a base path to resolve a relative location they mentioned.
    """
    return f"current directory: {os.getcwd()}"


def append_to_file(file_path: str, content: str) -> str:
    """Append text to the end of a file, creating it if it does not exist.

    Use this for logs, notes, and lists that grow over time -- anything where
    overwriting (write_file) would destroy what is already there.

    Args:
        file_path: Absolute path of the file to append to.
        content: The text to add at the end of the file.
    """
    path = Path(file_path)
    existed = path.is_file()
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)
    action = "appended to" if existed else "created and wrote to"
    return f"{action} {file_path} ({len(content)} characters added)"
