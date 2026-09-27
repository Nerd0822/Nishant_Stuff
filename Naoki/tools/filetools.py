import os

from langchain_core.tools import tool

from config import MAX_READ

from .common import ROOT, _resolve


@tool
def get_current_directory() -> str:
    """Return the current working directory and project root."""
    return f"cwd={os.getcwd()}\nroot={ROOT}"


@tool
def list_files(directory: str = ".", limit: int = 100) -> str:
    """List files in a directory, relative to project root. Args: directory, limit."""
    try:
        base = _resolve(directory)
    except ValueError as e:
        return f"bad path: {e}"
    try:
        if not base.exists():
            return f"not found: {base}"
        if not base.is_dir():
            return f"not a directory: {base}"
        entries = sorted(base.iterdir())[:limit]
    except OSError as e:
        return f"list error: {e}"
    lines = [f"{'[d]' if e.is_dir() else '[f]'} {e.name}" for e in entries]
    return "\n".join(lines) if lines else "(empty)"


@tool
def read_file(path: str, offset: int = 0, limit: int = 200) -> str:
    """Read a text file with line offset/limit. Args: path, offset (0-based), limit (lines)."""
    try:
        p = _resolve(path)
    except ValueError as e:
        return f"bad path: {e}"
    if not p.is_file():
        return f"not a file: {p}"
    try:
        size = p.stat().st_size
    except OSError as e:
        return f"stat error: {e}"
    if size > MAX_READ * 10:
        return f"file too large ({size} bytes), use offset/limit"
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except (OSError, ValueError, UnicodeError) as e:
        return f"read error: {type(e).__name__}: {e}"
    lines = text.splitlines()
    chunk = lines[offset : offset + limit]
    return "\n".join(f"{i + offset + 1}: {l}" for i, l in enumerate(chunk)) or "(empty file)"


@tool
def file_info(path: str) -> str:
    """Return size, mtime, type for a path."""
    try:
        p = _resolve(path)
        if not p.exists():
            return f"not found: {p}"
        st = p.stat()
    except ValueError as e:
        return f"bad path: {e}"
    except OSError as e:
        return f"stat error: {type(e).__name__}: {e}"
    kind = "dir" if p.is_dir() else "file"
    return f"{kind} {p}\nsize={st.st_size}\nmtime={st.st_mtime}"


@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a text file. Args: path, content. Creates parent dirs."""
    try:
        p = _resolve(path)
    except ValueError as e:
        return f"bad path: {e}"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} chars to {p}"
    except (OSError, ValueError) as e:
        return f"write error: {type(e).__name__}: {e}"


@tool
def create_file(path: str, content: str = "") -> str:
    """Create a new text file, fail if it already exists. Use write_file to overwrite. Args: path, content."""
    try:
        p = _resolve(path)
    except ValueError as e:
        return f"bad path: {e}"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "x", encoding="utf-8") as f:
            f.write(content)
        return f"created {p} ({len(content)} chars)"
    except FileExistsError:
        return f"exists, not overwritten: {p}"
    except (OSError, ValueError) as e:
        return f"create error: {type(e).__name__}: {e}"


@tool
def make_dir(path: str) -> str:
    """Create a directory (including parents). Args: path."""
    try:
        p = _resolve(path)
    except ValueError as e:
        return f"bad path: {e}"
    try:
        p.mkdir(parents=True, exist_ok=True)
        return f"ok: {p}"
    except (OSError, ValueError) as e:
        return f"mkdir error: {type(e).__name__}: {e}"
