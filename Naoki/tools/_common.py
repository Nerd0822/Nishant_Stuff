"""Small shared helpers for the toolbelt."""

from config import MAX_TOOL_CHARS


def _truncate(text: str, limit: int = MAX_TOOL_CHARS) -> str:
    # Tool output feeds the model prompt, so unbounded output means a
    # blown context window and a slow local model. Cut early, say by how
    # much, and let the model ask for a narrower read instead.
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated; {len(text) - limit} more characters]"
