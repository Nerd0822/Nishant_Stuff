"""Desktop tools: launching files and clipboard access."""

import shutil
import subprocess
from pathlib import Path

from ._common import tool


@tool
def launch_file(path: str) -> str:
    """Open a file or directory with the desktop's default application.

    Use this when the user says 'open' or 'show' something -- a PDF, image,
    screenshot, or folder in the file manager. Runs detached via xdg-open
    so it never blocks the assistant; returns immediately after launching.
    (To read a file's contents for yourself, use read_file instead.)

    Args:
        path: Absolute path of the file or directory to open.
    """
    target = Path(path)
    if not target.exists():
        return f"{path} does not exist"
    subprocess.Popen(
        ["xdg-open", str(target)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return f"opened {path} with the default application"


@tool
def copy_to_clipboard(text: str) -> str:
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
