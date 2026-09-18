import os
import shutil
from pathlib import Path


def read_file(file_path):
    try:
        with open(file_path) as f:
            return f.read()
    except (FileNotFoundError, PermissionError, OSError) as e:
        return str(e)


def write_file(file_path, data):
    p = Path(file_path)
    if p.is_file():
        try:
            backup_path = p.with_name(f"{p.stem}_copy{p.suffix}")
            shutil.copy2(p, backup_path)
        except OSError as e:
            return f"backup failed: {e}"
    try:
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(data,encoding="utf-8")
        return  f"wrote {len(data)} chars to {file_path}"
    except (OSError,PermissionError) as e:
        return str(e)

def create_file(file_path, data=""):
    p = Path(file_path).expanduser()
    if p.exists():
        return f"{file_path} already exists; use write_file or edit_file to modify it"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data, encoding="utf-8")
        return f"created {file_path} ({len(data)} chars)"
    except (OSError, PermissionError) as e:
        return str(e)


def list_files(dir_path):
    try:
        return os.listdir(dir_path)
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError) as e:
        return str(e)


def get_current_dir():
    try:
        return str(Path.cwd())
    except OSError as e:
        return str(e)


def delete_file(file_path, recursive=False):
    p = Path(file_path).expanduser()
    try:
        if not p.exists():
            return f"source does not exist: {file_path}"
        if p.is_dir():
            if any(p.iterdir()) and not recursive:
                return f"{file_path} is a non-empty directory; pass recursive=True to delete it"
            shutil.rmtree(p) if recursive else p.rmdir()
        else:
            p.unlink()
        return f"deleted {file_path}"
    except (FileNotFoundError, PermissionError, OSError) as e:
        return str(e)


def mkdir(dir_path):
    p = Path(dir_path).expanduser()
    try:
        p.mkdir(parents=True, exist_ok=True)
        return f"created directory {p}"
    except (OSError, PermissionError) as e:
        return str(e)


def move_file(src, dest):
    s = Path(src).expanduser()
    d = Path(dest).expanduser()
    try:
        if not s.exists():
            return f"source does not exist: {src}"
        d.parent.mkdir(parents=True, exist_ok=True)
        s.rename(d)
        return f"moved {src} to {dest}"
    except (FileNotFoundError, PermissionError, OSError) as e:
        return str(e)


def copy_file(src, dest):
    s = Path(src).expanduser()
    d = Path(dest).expanduser()
    try:
        if not s.exists():
            return f"source does not exist: {src}"
        d.parent.mkdir(parents=True, exist_ok=True)
        if s.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
        return f"copied {src} to {dest}"
    except (FileNotFoundError, PermissionError, OSError) as e:
        return str(e)


def count_lines(file_path):
    p = Path(file_path).expanduser()
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        words = len(text.split())
        chars = len(text)
        return f"lines={len(lines)} words={words} chars={chars}"
    except (FileNotFoundError, PermissionError, OSError) as e:
        return str(e)


ALL_TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "create_file": create_file,
    "list_files": list_files,
    "get_current_dir": get_current_dir,
    "delete_file": delete_file,
    "mkdir": mkdir,
    "move_file": move_file,
    "copy_file": copy_file,
    "count_lines": count_lines,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read any file",
            "parameters": {
                "type": "object",
                "required": ["file_path"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Edit any file",
            "parameters": {
                "type": "object",
                "required": ["file_path", "data"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file",
                    },
                    "data": {
                        "type": "string",
                        "description": "The data you want to write in the file",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file with content. Fails if the file already exists — use write_file or edit_file to modify an existing one.",
            "parameters": {
                "type": "object",
                "required": ["file_path"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the new file to create",
                    },
                    "data": {
                        "type": "string",
                        "description": "Content to write into the new file (default: empty file)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in a path",
            "parameters": {
                "type": "object",
                "required": ["dir_path"],
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "The path to the directory",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_dir",
            "description": "Get the current working directory path",
            "parameters": {
                "type": "object",
                "required": [],
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file or empty-ish directory",
            "parameters": {
                "type": "object",
                "required": ["file_path"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file (or directory) to delete",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mkdir",
            "description": "Create a new directory (with optional parents)",
            "parameters": {
                "type": "object",
                "required": ["dir_path"],
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "The path of the directory to create",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move or rename a file/directory",
            "parameters": {
                "type": "object",
                "required": ["src", "dest"],
                "properties": {
                    "src": {
                        "type": "string",
                        "description": "Path of the existing source file/directory",
                    },
                    "dest": {
                        "type": "string",
                        "description": "Destination path to move it to",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file (preserving metadata)",
            "parameters": {
                "type": "object",
                "required": ["src", "dest"],
                "properties": {
                    "src": {
                        "type": "string",
                        "description": "Path of the existing source file/directory",
                    },
                    "dest": {
                        "type": "string",
                        "description": "Destination path to copy it to",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_lines",
            "description": "Count lines, words, and characters in a file",
            "parameters": {
                "type": "object",
                "required": ["file_path"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to analyze",
                    },
                },
            },
        },
    },
]

# todo:
# fix the tools like search file and some newer tools and add more tools, also the model stops in between the task
