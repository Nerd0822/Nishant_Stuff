"""Reasoning tools: delegating hard work to the advanced local model."""

import ollama

from .. import models
from ..config import ADVANCED_KEEP_ALIVE, ADVANCED_MODEL, SWAP_MODELS
from .registry import tool


@tool
def ask_expert(task: str) -> str:
    """Delegate a difficult task to the advanced model.

    Use for hard reasoning, careful coding, or long analysis that the primary
    model may get wrong. The advanced model cannot see this conversation, so
    include every relevant detail inside `task`.
    """
    if SWAP_MODELS:
        # Evict the primary model so only the advanced model is in memory.
        models.unload_others(ADVANCED_MODEL)
    response = ollama.chat(
        model=ADVANCED_MODEL,
        messages=[{"role": "user", "content": task}],
        think=False,
        keep_alive=ADVANCED_KEEP_ALIVE,
    )
    return response.message.content or ""


# Legacy name kept importable (not advertised) for backward compatibility.
def delegate_to_advanced_model(task: str) -> str:
    """Deprecated alias for ask_expert."""
    return ask_expert(task)