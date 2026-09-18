import subprocess

from langchain_core.tools import Tool


def shell_command_tool(command: str) -> str:
    """Execute a shell command and return its output.
    Only non-interactive commands are allowed (no sudo, no interactive prompts)."""
    try:
        # Safety: block dangerous commands
        blocked_prefixes = ["sudo", "su ", "passwd", "rm -rf /", "dd ", ":(){ :|:& };:"]
        cmd_lower = command.strip().lower()
        for blocked in blocked_prefixes:
            if cmd_lower.startswith(blocked):
                return f"Error: Command '{blocked}' is blocked for safety."

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"

        # Limit output length
        if len(output) > 5000:
            output = output[:5000] + "\n... (output truncated)"

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


shell_tools = [
    Tool(
        name="shell_command",
        func=shell_command_tool,
        description=(
            "Execute a shell command. Input: a valid shell command string. "
            "Useful for running scripts, checking system info, or file operations. "
            "Blocked: sudo, su, destructive system commands."
        ),
    ),
]
