"""Tool registry: imports every category module and exposes the TOOLS dict.

Category modules register their tools via the @tool decorator in registry.py.
This package only imports those modules (so the decorators run) and exposes
the assembled TOOLS dict the agent loop advertises to Ollama.

Add a tool by writing it in its category module with @tool -- no edits needed
here.
"""

from . import desktop, filesystem, memory, reasoning, system, web  # noqa: F401
from .registry import REGISTRY

# Single source of truth for the agent's tools (name -> function).
# Keys match function names: that is the name Ollama advertises to the
# model and the name that comes back in tool_call.function.name.
TOOLS: dict = dict(REGISTRY)
assert all(name == fn.__name__ for name, fn in TOOLS.items()), (
    "TOOLS keys must match their function names"
)

__all__ = ["TOOLS"]