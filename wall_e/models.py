"""Model lifecycle: keep one model resident at a time to avoid memory pressure.

Ollama loads a model on first use and evicts it after `keep_alive` of
inactivity. Holding the primary and advanced model in memory at once can
exhaust VRAM, so callers evict the other model before loading their own (see
agent.py and tools/reasoning.py).

Unloads are best-effort: a failure is swallowed and simply leaves the model
resident, which is always safe.
"""

import ollama

from .config import ADVANCED_MODEL, MODEL_CMD_TIMEOUT, PRIMARY_MODEL

MANAGED_MODELS = (PRIMARY_MODEL, ADVANCED_MODEL)

# Lifecycle calls must never hang the CLI (Ollama queues requests while a
# model is busy), so give ps/unload a short timeout instead of the default
# "wait forever".
_client = ollama.Client(timeout=MODEL_CMD_TIMEOUT)


def loaded_models() -> list[str]:
    """Names of the models Ollama currently has in memory."""
    try:
        return [entry.model for entry in _client.ps().models]
    except Exception:
        return []


def unload_model(model_name: str) -> bool:
    """Evict one model from memory. Returns False if the call failed."""
    try:
        _client.generate(model=model_name, prompt="", keep_alive=0)
        return True
    except Exception:
        return False


def unload_others(keep: str) -> None:
    """Evict every loaded model except `keep`."""
    for name in loaded_models():
        if name != keep:
            unload_model(name)


def unload_all() -> None:
    """Evict every loaded model (used by /unload and on exit)."""
    for name in loaded_models():
        unload_model(name)
