"""Shared helpers for Naoki's tool subpackage."""

from config import MAX_TOOL_CHARS


def _truncate(text: str, limit: int = MAX_TOOL_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated; {len(text) - limit} more characters]"
