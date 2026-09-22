"""Tool registration and shared helpers for the tools subpackage.

Functions decorated with @tool are auto-registered into REGISTRY. The
tools/__init__.py imports every category module (so the decorators run) and
exposes TOOLS = dict(REGISTRY) to the agent loop.
"""

from ..config import MAX_TOOL_CHARS

REGISTRY: dict = {}


def tool(fn):
    """Mark a function as an agent tool (auto-registered by name)."""
    REGISTRY[fn.__name__] = fn
    return fn


def _truncate(text: str, limit: int = MAX_TOOL_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated; {len(text) - limit} more characters]"