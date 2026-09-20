"""Shell and system tools: commands and machine information."""

import os
import platform
import shutil
import subprocess

from config import COMMAND_TIMEOUT

from ._common import _truncate


def system_info() -> str:
    """Report OS, CPU, memory, disk, uptime, and desktop session details.

    No arguments. Use this instead of guessing about the user's machine, and
    before running anything resource-heavy so you know what you are working
    with. Never invent specs -- call this.
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


def run_command(command: str) -> str:
    """Run a shell command on this machine and return its output.

    Use this for tasks the other tools cannot do (installed programs, git,
    system information). Commands are killed if they run too long. Prefer
    read-only commands; never run destructive commands unless the user
    explicitly asked for them.

    Args:
        command: The shell command to run, exactly as typed in a terminal.
    """
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=COMMAND_TIMEOUT
    )
    output = f"{result.stdout}{result.stderr}".strip()
    return _truncate(f"exit code {result.returncode}\n{output}", 4000)
