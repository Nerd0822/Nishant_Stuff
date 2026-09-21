"""Wall-e's tools, grouped by category.

Category modules (filesystem, system, desktop, web, memory, reasoning)
register their tools via the @tool decorator in tools/_common.py; this
package only imports those modules (so the decorators run) and exposes
the assembled TOOLS dict the agent loop advertises to Ollama. Add a tool
by writing it in its category module with @tool -- no edits needed here.

Legacy aliases (search_google, search_wikipedia, delegate_to_advanced_model,
old file/shell names) stay importable from their modules but are NOT in
TOOLS, keeping the advertised schema small for the local model.
"""

from . import desktop, filesystem, memory, reasoning, system, web  # noqa: F401
from ._common import REGISTRY

# Single source of truth for the agent's tools (name -> function).
# Keys match function names: that is the name Ollama advertises to the
# model and the name that comes back in tool_call.function.name.
TOOLS: dict = dict(REGISTRY)
assert all(name == fn.__name__ for name, fn in TOOLS.items()), (
    "TOOLS keys must match their function names"
)

__all__ = ["TOOLS"]
