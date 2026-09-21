"""Memory tools: durable user facts and quick notes."""

from datetime import datetime
from pathlib import Path

from helper import append_user_info

from ._common import tool


@tool
def remember_fact(info: str) -> str:
    """Save a durable fact about the user the moment they share one.

    Call this proactively, BEFORE answering. Example: if the user says their
    name is Nishant, call remember_fact with that fact right away. One
    fact per call -- a message with three facts needs three calls. The user
    never needs to ask you to remember. Skip secrets, small talk, and
    temporary details.

    Args:
        info: One short sentence describing the fact to remember.
    """
    if append_user_info(info):
        return f"remembered: {info}"
    return f"already known or empty, nothing stored: {info}"


@tool
def save_note(note: str) -> str:
    """Save a timestamped note to the user's notes file (~/notes.txt).

    Use this when the user says "note this down", "remind me", or shares
    something to keep -- a TODO, an idea, a command to try later. Appends,
    never overwrites; each entry gets a date-time stamp.

    Args:
        note: The text of the note to save.
    """
    notes_file = Path.home() / "notes.txt"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(notes_file, "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {note.rstrip()}\n")
    return f"noted in {notes_file}"
