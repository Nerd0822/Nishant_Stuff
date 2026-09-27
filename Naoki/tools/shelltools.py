import subprocess

from langchain_core.tools import tool

from config import SHELL_TIMEOUT

from .common import ROOT


@tool
def run_shell(command: str, timeout: int = SHELL_TIMEOUT) -> str:
    """Run a read-only-ish shell command and return output. Use for ls, cat, grep, git status. Timeout seconds."""
    try:
        r = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT), check=False
        )
        out = (r.stdout or "")[-4000:]
        err = (r.stderr or "")[-1000:]
        return f"exit={r.returncode}\n{out}\n{err}".strip()
    except subprocess.TimeoutExpired:
        return "timeout"
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        return f"shell error: {type(e).__name__}: {e}"
