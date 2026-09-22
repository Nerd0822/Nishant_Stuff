"""Memory tools: durable user facts and quick notes."""

from datetime import datetime
from pathlib import Path

from ..conversation import append_user_info
from .registry import tool


@tool
def remember_fact(info: str) -> str:
    """Save a durable fact about the user the moment they share one.

    Call proactively, BEFORE answering. One fact per call -- a message with
    three facts needs three calls. Skip secrets, small talk, and temporary
    details.
    """
    if append_user_info(info):
        return f"remembered: {info}"
    return f"already known or empty, nothing stored: {info}"


@tool
def save_note(note: str) -> str:
    """Save a timestamped note to the user's notes file (~/notes.txt).

    Appends, never overwrites; each entry gets a date-time stamp.
    """
    notes_file = Path.home() / "notes.txt"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(notes_file, "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {note.rstrip()}\n")
    return f"noted in {notes_file}"