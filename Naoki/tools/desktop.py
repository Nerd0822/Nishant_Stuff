"""Desktop tools: opening files, clipboard, and quick notes."""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def open_file(file_path: str) -> str:
    """Open a file or directory with the desktop's default application.

    Use this when the user says 'open' something -- a PDF, image, folder in
    the file manager, URL target they downloaded. Runs detached via xdg-open
    so it never blocks the assistant; returns immediately after launching.

    Args:
        file_path: Absolute path of the file or directory to open.
    """
    path = Path(file_path)
    if not path.exists():
        return f"{file_path} does not exist"
    subprocess.Popen(
        ["xdg-open", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return f"opened {file_path} with the default application"


def clipboard_copy(text: str) -> str:
    """Copy text to the system clipboard (Wayland and X11 supported).

    Use this when the user says "copy this to my clipboard" -- a command, a
    password they generated elsewhere, an address. Reads nothing back.

    Args:
        text: The exact text to place on the clipboard.
    """
    for command in (["wl-copy"], ["xclip", "-selection", "clipboard"]):
        if shutil.which(command[0]) is None:
            continue
        try:
            subprocess.run(command, input=text, text=True, check=True, timeout=10)
            return f"copied {len(text)} characters to the clipboard"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return "no clipboard tool found (need wl-copy for Wayland or xclip for X11)"


def take_note(note: str) -> str:
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
