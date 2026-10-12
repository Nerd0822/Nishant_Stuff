"""Shell tools."""

import subprocess

from langchain_core.tools import tool

from config import SHELL_TIMEOUT


@tool
def run_command(command: str) -> str:
    """Run a shell command and return its stdout, stderr, and exit code.

    Blocks until the command finishes, so an interactive command (vim, top, ssh
    with no host) hangs until the timeout kills it. Args: command.
    """
    # ponytail: SHELL_TIMEOUT is the only hang guard -- a denylist of
    # interactive commands would fail fast instead of waiting it out. Add one
    # if the wait actually annoys.
    r = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=SHELL_TIMEOUT
    )
    return f"exit={r.returncode}\n{r.stdout}{r.stderr}"