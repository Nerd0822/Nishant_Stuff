"""Long-term memory: one JSON list of facts in about_me.json.

Kept as plain JSON (not a database) because the whole thing is read every
turn and a human can open it. Same format as the original Naoki, so facts
saved by the old version carry over untouched. One fact per line-item;
dedupe is exact-match, which is crude but predictable.
"""

import json
from pathlib import Path

ABOUT_ME_FILE = Path(__file__).resolve().parent / "about_me.json"


def load_user_info() -> list[str]:
    if not ABOUT_ME_FILE.exists():
        return []
    try:
        data = json.loads(ABOUT_ME_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(item) for item in data] if isinstance(data, list) else []


def add_fact(info: str) -> str:
    """Append one fact unless it's blank or already stored."""
    info = " ".join(str(info).split())
    if not info:
        return f"already known or empty, nothing stored: {info}"
    facts = load_user_info()
    if info in facts:
        return f"already known or empty, nothing stored: {info}"
    facts.append(info)
    try:
        ABOUT_ME_FILE.write_text(
            json.dumps(facts, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        return f"could not save: {info}"
    try:
        from rag import build_index

        build_index()
    except Exception:
        pass  # search index is a nice-to-have; memory itself already saved
    return f"remembered: {info}"


def get_facts() -> list[str]:
    return load_user_info()


def save_note(note: str) -> str:
    """Append a timestamped line to ~/notes.txt. Never overwrites."""
    from datetime import datetime

    notes_file = Path.home() / "notes.txt"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(notes_file, "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {note.rstrip()}\n")
    return f"noted in {notes_file}"
