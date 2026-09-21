"""Shared helpers for Wall-e's tool subpackage.

Any function decorated with @tool is auto-registered into REGISTRY.
tools/__init__.py imports every category module (so the decorators run)
then exposes TOOLS = dict(REGISTRY) to the agent loop. To add a tool,
write it in its category module and add @tool -- no manual dict edits.
"""

from config import MAX_TOOL_CHARS

REGISTRY: dict = {}


def tool(fn):
    """Mark a function as an agent tool (auto-registered by name)."""
    REGISTRY[fn.__name__] = fn
    return fn


def _truncate(text: str, limit: int = MAX_TOOL_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated; {len(text) - limit} more characters]"
