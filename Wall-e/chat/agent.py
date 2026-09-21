"""
Agent integration for the Wall-e Django web app.

This module adapts the existing Wall-e agent logic (config, prompt, tools)
for use inside Django views.  It calls the local Ollama model, handles
tool calls, and returns the assistant's text response.

Key differences from the original ``core.py`` agent loop:
- Conversation history is passed in as a parameter (loaded from the DB)
  instead of being stored in a global list.
- Tool-call / tool-result pairs are processed internally; only the final
  text reply is returned to the caller.
- Tool-execution events can be streamed back via the ``on_tool_event``
  callback for rich UI feedback (e.g. showing which tool was called).
"""

from __future__ import annotations

import ollama

from config import (
    MAX_MESSAGES,
    MAX_PREDICT_TOKENS,
    MAX_NUM_CTX,
    MAX_TURNS,
    PRIMARY_MODEL,
)
from helper import load_user_info
from prompt import build_system_prompt
from tools import TOOLS


def _build_ollama_options() -> dict:
    """Build the Ollama ``options`` dict from config.py settings."""
    opts: dict = {"num_predict": MAX_PREDICT_TOKENS}
    if MAX_NUM_CTX is not None:
        opts["num_ctx"] = MAX_NUM_CTX
    return opts


def get_response(
    user_message: str,
    prev_messages: list[dict],
    on_tool_event=None,
) -> str:
    """Generate an AI reply via the local Ollama model.

    Parameters
    ----------
    user_message
        The new message from the user (a plain string).
    prev_messages
        List of ``{"role": str, "content": str}`` dicts representing the
        conversation history (loaded from the database).
    on_tool_event
        Optional callback ``(kind, tool_name, payload)`` that is invoked
        when the model requests a tool call (``"call"``) or when a tool
        returns its result (``"result"``).

    Returns
    -------
    str
        The assistant's final text response.
    """
    # --- Build the full message list for Ollama ---------------------------
    facts = load_user_info()
    system_prompt = build_system_prompt(facts)

    messages: list = [{"role": "system", "content": system_prompt}]

    # Append conversation history (respect MAX_MESSAGES window)
    history = prev_messages
    if history and MAX_MESSAGES:
        messages.extend(history[-MAX_MESSAGES:])
    elif history:
        messages.extend(history)

    # Add the new user message
    messages.append({"role": "user", "content": user_message})

    opts = _build_ollama_options()
    tool_list = list(TOOLS.values())

    # --- Agent loop: model → tools → results → final answer ---------------
    for _ in range(MAX_TURNS):
        response = ollama.chat(
            model=PRIMARY_MODEL,
            messages=messages,
            tools=tool_list,
            options=opts,
        )

        assistant_msg = response.message
        messages.append(assistant_msg)

        # No tool calls → this is the final answer
        if not assistant_msg.tool_calls:
            return assistant_msg.content or ""

        # Process each tool call the model returned
        for tool_call in assistant_msg.tool_calls:
            tool_name = tool_call.function.name
            tool_args = dict(tool_call.function.arguments)

            if on_tool_event is not None:
                on_tool_event("call", tool_name, tool_args)

            tool_fn = TOOLS.get(tool_name)
            if tool_fn is None:
                tool_result = f"unknown tool: {tool_name}"
            else:
                try:
                    tool_result = str(tool_fn(**tool_args))
                except Exception as exc:  # noqa: BLE001
                    tool_result = f"tool error: {type(exc).__name__}: {exc}"

            # Feed the tool result back to the model
            messages.append(
                {
                    "role": "tool",
                    "content": tool_result,
                }
            )

            if on_tool_event is not None:
                on_tool_event("result", tool_name, tool_result)

    # If we exhausted MAX_TURNS without a final text answer
    return f"(stopped after {MAX_TURNS} rounds of tool calls without a final answer)"