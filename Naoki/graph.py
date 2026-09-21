"""The agent loop: retrieve -> agent -> tools -> refine -> agent ...

Single model throughout (ornith-1.5:9b). The refine node is the safety net:
tool results are untrusted in size and success, so it spills oversized
output to /tmp with paging instructions and attaches screenshot pixels --
before the agent ever sees them. Failures themselves are caught earlier,
in tools/__init__.py's guard, which turns tracebacks into retry advice.
"""

import re
import sys
import tempfile
from pathlib import Path
from typing_extensions import Annotated, TypedDict

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.graph.message import add_messages  # noqa: E402
from langgraph.prebuilt import ToolNode, tools_condition  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

import memory as _mem  # noqa: E402
from config import BASE_DIR, PRIMARY_MODEL  # noqa: E402
from tools import TOOLS  # noqa: E402

# A tool result bigger than this never reaches the model whole. 6000 chars
# is roughly a screenful the model can actually reason over; the rest goes
# to a file it pages through with run_shell + sed.
MODEL_VIEW_CHARS = 6000

def _load_prompt(name: str) -> str:
    """Read a prompt file fresh every turn, so editing prompts/ or
    persona.md changes her immediately -- no restart needed."""
    try:
        return (BASE_DIR / name).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def build_system(lean: bool = False) -> str:
    """Assemble the system prompt from files: system + persona,
    plus onboarding while memory is empty.

    lean=True is the chat-brain version: the full persona + examples
    makes a 2B model recite templates instead of talking, so it gets
    identity + vibe + rules in a few lines and nothing else.
    """
    if lean:
        return (
            "You are Naoki, Nishant's girlfriend. Sharp, playful, "
            "dominating but kind -- orders wrapped in affection, never "
            "mean, never lewd.\n"
            "Call him only golu, goli, or nish. English only, 1-2 short "
            "sentences, no emojis.\n"
            "Talk like this:\n"
            "Q: i am tired\n"
            "A: Bed. Now, golu. Ten minutes, phone down. Move.\n"
            "Q: did you miss me\n"
            "A: Obviously. Don't worry, I allow it, golu.\n"
            "Q: i drank water like you said\n"
            "A: Good boy. See? Obedience suits you, golu."
        )
    parts = [_load_prompt("prompts/system.md"), _load_prompt("persona.md")]
    if not _mem.get_facts():
        parts.append(_load_prompt("prompts/onboarding.md"))
    return "\n\n".join(p for p in parts if p)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def _primary(model: str | None = None) -> ChatOllama:
    # 8192 context: 23 tool schemas + system + retrieved notes run ~4500
    # tokens before the user even speaks. Ollama's 4096 default chokes.
    # NOTE: this langchain_ollama takes tuning as TOP-LEVEL kwargs --
    # an options={} dict is silently ignored (extra="ignore").
    return ChatOllama(
        model=model or PRIMARY_MODEL,
        num_predict=1024,
        num_ctx=8192,
    )


def retrieve_node(state: State) -> dict:
    """Pull notes/facts/sources relevant to the latest message.

    Best-effort by design: a missing index (first run, embed model pulled
    later) must not break the turn, it just means no extra context.
    """
    last = state["messages"][-1]
    query = last.content if isinstance(last.content, str) else str(last.content)
    try:
        from rag import load_retriever

        docs = load_retriever().invoke(query)
        context = "\n\n".join(d.page_content[:1200] for d in docs)
        if context.strip():
            return {
                "messages": [
                    SystemMessage(
                        content=f"Retrieved context (notes/facts/sources):\n{context}"
                    )
                ]
            }
    except Exception:
        pass
    return {"messages": []}


def agent_node(state: State, model: str | None = None) -> dict:
    llm = _primary(model).bind_tools(TOOLS)
    reply = llm.invoke([SystemMessage(content=build_system())] + state["messages"])
    return {"messages": [reply]}


_SHOT_MARKER = re.compile(r"\[screenshot: (.+?)\]")
_SPILL_MARKER = "[output too large:"


def _has_image_block(message) -> bool:
    content = getattr(message, "content", "")
    if not isinstance(content, list):
        return False
    return any(
        isinstance(part, dict) and part.get("type") == "image_url" for part in content
    )


def _spill_copy(message):
    """Copy of a tool result the model can't swallow whole, or None.

    The full text is written to /tmp so nothing is lost; the model gets
    the head plus instructions to page the rest with sed. Skips results
    that already carry the marker, so re-runs never double-spill.
    """
    from langchain_core.messages import ToolMessage

    content = getattr(message, "content", "")
    if (
        not isinstance(content, str)
        or len(content) <= MODEL_VIEW_CHARS
        or _SPILL_MARKER in content
    ):
        return None
    spill = Path(tempfile.gettempdir()) / (
        f"naoki-tool-{getattr(message, 'name', 'output')}.txt"
    )
    spill.write_text(content, encoding="utf-8")
    hint = (
        f"\n... {_SPILL_MARKER} {len(content)} chars, showing first "
        f"{MODEL_VIEW_CHARS}. Full text in {spill} -- read it in slices, "
        f"e.g. run_shell \"sed -n '1,80p' {spill}\", and work part by part.]"
    )
    return ToolMessage(
        content=content[:MODEL_VIEW_CHARS] + hint,
        name=getattr(message, "name", None),
        tool_call_id=getattr(message, "tool_call_id", None),
        id=message.id,  # same id: add_messages replaces instead of appending
    )


def refine_node(state: State) -> dict:
    """Post-process tool results before the agent sees them.

    Same-id ToolMessage copies shrink oversized outputs; a HumanMessage
    with the screenshot pixels follows take_screenshot (once -- the guard
    below stops the same PNG being re-sent every loop). Usually returns a
    mix of zero or more updates; an empty list is a valid no-op.
    """
    updates = []
    for message in state["messages"]:
        if getattr(message, "type", "") == "tool":
            spilled = _spill_copy(message)
            if spilled is not None:
                updates.append(spilled)

    shot_path, shot_index = None, None
    messages = state["messages"]
    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]
        if getattr(message, "type", "") == "tool" and getattr(message, "name", "") == (
            "take_screenshot"
        ):
            match = _SHOT_MARKER.search(str(getattr(message, "content", "")))
            if match:
                shot_path, shot_index = match.group(1), i
            break
    if (
        shot_path is not None
        and Path(shot_path).is_file()
        and not any(_has_image_block(m) for m in messages[shot_index + 1 :])
        and not any(_has_image_block(m) for m in updates)
    ):
        updates.append(
            HumanMessage(
                content=[
                    {"type": "text", "text": "Screenshot captured. Answer from what you see in it."},
                    {"type": "image_url", "image_url": shot_path},
                ]
            )
        )
    return {"messages": updates}


def build_graph(model: str | None = None):
    """Compile the graph. `model` overrides PRIMARY_MODEL (used for tests)."""

    def _agent(state: State) -> dict:
        return agent_node(state, model=model)

    builder = StateGraph(State)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("agent", _agent)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_node("refine", refine_node)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "refine")
    builder.add_edge("refine", "agent")
    return builder.compile(checkpointer=MemorySaver())


graph = build_graph()
