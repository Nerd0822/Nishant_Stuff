"""The machine itself: shell, specs, screenshots.

run_shell is the escape hatch for everything the other tools can't do --
prefer the specific tools first, because their output is structured and
their failure modes are kinder than raw shell text.
"""

import os
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from config import COMMAND_TIMEOUT

from ._common import _truncate


def run_shell(command: str) -> str:
    """Run a shell command, return exit code plus output (capped at 4000 chars).

    Killed after COMMAND_TIMEOUT. Read-only commands are always fine;
    anything destructive needs the user to have asked for it explicitly.

    Args:
        command: The shell command, exactly as typed in a terminal.
    """
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=COMMAND_TIMEOUT
    )
    output = f"{result.stdout}{result.stderr}".strip()
    return _truncate(f"exit code {result.returncode}\n{output}", 4000)


def host_info() -> str:
    """One-line-per-fact summary of this machine: OS, CPU, RAM, disk, session.

    No arguments. The model must call this instead of guessing specs --
    wrong guesses about the OS or desktop have caused real bad commands.
    """
    uname = platform.uname()
    lines = [
        f"os: {uname.system} {uname.release} ({platform.freedesktop_os_release().get('PRETTY_NAME', uname.version)})",
        f"machine: {uname.machine} ({os.cpu_count()} CPUs), hostname {uname.node}",
    ]
    try:
        mem = {}
        with open("/proc/meminfo", encoding="utf-8") as f:
            for row in f:
                key, _, value = row.partition(":")
                mem[key.strip()] = value.split()[0]
        total = int(mem["MemTotal"]) // 1024
        free = int(mem["MemAvailable"]) // 1024
        lines.append(f"memory: {total - free} MB used of {total} MB")
    except (OSError, KeyError, ValueError, IndexError):
        pass
    try:
        disk = shutil.disk_usage("/")
        lines.append(f"disk (/): {disk.used // 10**9} GB used of {disk.total // 10**9} GB")
    except OSError:
        pass
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            seconds = int(float(f.read().split()[0]))
        hours, remainder = divmod(seconds, 3600)
        lines.append(f"uptime: {hours}h {remainder // 60}m")
    except (OSError, ValueError):
        pass
    lines.append(
        f"session: {os.environ.get('XDG_CURRENT_DESKTOP', 'unknown desktop')} "
        f"({os.environ.get('XDG_SESSION_TYPE', 'unknown session')}), "
        f"user {os.environ.get('USER', 'unknown')}"
    )
    return _truncate("\n".join(lines))


def _screenshot_commands(output: Path) -> list[list[str]]:
    # Ordered by what this box actually runs: KDE Wayland first, then
    # generic Wayland, then X11 tools. First installed binary wins.
    return [
        ["spectacle", "-b", "-n", "-o", str(output)],
        ["grim", str(output)],
        ["scrot", str(output)],
        ["import", "-window", "root", str(output)],
        ["gnome-screenshot", "-f", str(output)],
        ["maim", str(output)],
    ]


def take_screenshot(target: str = "screen") -> str:
    """Capture the screen to a PNG in /tmp, return its path and dimensions.

    The result carries a `[screenshot: <path>]` marker. The graph watches
    for it and feeds the pixels to the model, which can genuinely see them
    (ornith ships a vision projector). `region` waits for the user to drag
    a selection, so prefer `screen` unless they asked for a region.

    Args:
        target: "screen" for the whole desktop, "window" for the active
            window, "region" for an interactive selection.
    """
    if target not in ("screen", "window", "region"):
        raise ValueError(f"target must be 'screen', 'window' or 'region', got '{target}'")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = Path(tempfile.gettempdir()) / f"naoki-screenshot-{stamp}.png"

    last_error = "no screenshot backend found"
    tried: list[str] = []
    for cmd in _screenshot_commands(output):
        if shutil.which(cmd[0]) is None:
            continue
        full = list(cmd)
        if target == "window" and cmd[0] == "spectacle":
            full = ["spectacle", "-b", "-n", "-a", "-o", str(output)]
        elif target == "region" and cmd[0] == "spectacle":
            full = ["spectacle", "-b", "-n", "-r", "-o", str(output)]
        elif target == "region" and cmd[0] == "import":
            full = ["import", str(output)]
        tried.append(cmd[0])
        try:
            subprocess.run(
                full, check=True, timeout=30,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            )
            if output.is_file() and output.stat().st_size > 0:
                break
            last_error = f"{cmd[0]} ran but produced no file"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            err = getattr(exc, "stderr", "") or str(exc)
            last_error = f"{cmd[0]} failed: {str(err).strip()[:200]}"
    else:
        return (
            f"screenshot failed ({last_error}). tried: "
            f"{', '.join(tried) or 'none installed'}; need one of "
            f"spectacle / grim / scrot / ImageMagick / gnome-screenshot / maim"
        )

    # Shrink huge captures: a 4K PNG wastes vision context for zero gain.
    dimensions = ""
    try:
        from PIL import Image

        with Image.open(output) as img:
            dimensions = f"{img.width}x{img.height}"
            if max(img.width, img.height) > 1600:
                img.thumbnail((1600, 1600))
                img.save(output, optimize=True)
    except Exception:
        pass
    size_kb = output.stat().st_size // 1024
    detail = f"{dimensions}, {size_kb} KB" if dimensions else f"{size_kb} KB"
    return f"[screenshot: {output}] saved ({detail}). Open it with launch_file to show the user."
