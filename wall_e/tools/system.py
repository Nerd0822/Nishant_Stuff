"""System tools: shell commands, host information, and screenshots."""

import os
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from ..config import COMMAND_TIMEOUT
from .registry import _truncate, tool


@tool
def run_shell(command: str) -> str:
    """Run a shell command on this machine and return its output.

    Use for tasks the other tools cannot do (installed programs, git, system
    info). Commands are killed if they run too long. Prefer read-only commands;
    never run destructive commands unless the user explicitly asked.
    """
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=COMMAND_TIMEOUT
    )
    output = f"{result.stdout}{result.stderr}".strip()
    return _truncate(f"exit code {result.returncode}\n{output}", 4000)


@tool
def host_info() -> str:
    """Report OS, CPU, memory, disk, uptime, and desktop session details."""
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
        lines.append(
            f"disk (/): {disk.used // 10**9} GB used of {disk.total // 10**9} GB"
        )
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


def _screenshot_candidates(output: Path) -> list[list[str]]:
    """Backend command chains, first available binary wins at runtime."""
    return [
        ["spectacle", "-b", "-n", "-o", str(output)],
        ["grim", str(output)],
        ["scrot", str(output)],
        ["import", "-window", "root", str(output)],
        ["gnome-screenshot", "-f", str(output)],
        ["maim", str(output)],
    ]


@tool
def take_screenshot(target: str = "screen") -> str:
    """Capture the screen and save it to a PNG file.

    Returns the saved file path plus dimensions. Pass that path to
    launch_file if the user wants to see it. Text-only models get only the
    path and metadata; vision models receive the pixels via agent.py.
    """
    if target not in ("screen", "window", "region"):
        raise ValueError(
            f"target must be 'screen', 'window' or 'region', got '{target}'"
        )
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = Path(tempfile.gettempdir()) / f"wall-e-screenshot-{stamp}.png"

    last_error = "no screenshot backend found"
    attempted: list[str] = []
    for cmd in _screenshot_candidates(output):
        if shutil.which(cmd[0]) is None:
            continue
        full_cmd = list(cmd)
        if target == "window" and cmd[0] == "spectacle":
            full_cmd = ["spectacle", "-b", "-n", "-a", "-o", str(output)]
        elif target == "region" and cmd[0] == "spectacle":
            full_cmd = ["spectacle", "-b", "-n", "-r", "-o", str(output)]
        elif target == "region" and cmd[0] == "import":
            full_cmd = ["import", str(output)]
        attempted.append(cmd[0])
        try:
            subprocess.run(
                full_cmd, check=True, timeout=30,
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
            f"{', '.join(attempted) or 'none installed'}; need one of "
            f"spectacle / grim / scrot / ImageMagick / gnome-screenshot / maim"
        )

    # Downscale huge captures so a future vision model gets a sane payload.
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
