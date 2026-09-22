"""Agent loop: runs one request through model -> tools -> answer."""

import re
from pathlib import Path

import ollama

from . import models
from .config import (
    MAX_MESSAGES,
    MAX_NUM_CTX,
    MAX_PREDICT_TOKENS,
    MAX_TURNS,
    PRIMARY_KEEP_ALIVE,
    PRIMARY_MODEL,
    SWAP_MODELS,
)
from .conversation import (
    conversation,
    create_user_message,
    load_user_info,
    save_history,
)
from .prompt import build_system_prompt
from .tools import TOOLS

_SCREENSHOT_MARKER = re.compile(r"\[screenshot: (.+?)\]")


def _screenshot_image(tool_name: str, result_text: str) -> str | None:
    """Return the screenshot file path if the tool result carries one."""
    if tool_name != "take_screenshot":
        return None
    match = _SCREENSHOT_MARKER.search(result_text)
    if not match:
        return None
    candidate = Path(match.group(1))
    return str(candidate) if candidate.is_file() else None


def _strip_screenshot_images() -> bool:
    """Drop attached images so a text-only model can be retried text-only."""
    removed = False
    for message in conversation:
        data = message if isinstance(message, dict) else message.model_dump()
        if isinstance(data, dict) and data.pop("images", None):
            removed = True
        if not isinstance(message, dict) and hasattr(message, "images"):
            try:
                message.images = None
            except Exception:
                pass
    return removed


def _model_options() -> dict:
    """Build Ollama options from config: num_predict caps output length,
    num_ctx optionally shrinks the context window."""
    opts = {"num_predict": MAX_PREDICT_TOKENS}
    if MAX_NUM_CTX is not None:
        opts["num_ctx"] = MAX_NUM_CTX
    return opts


def build_system_message() -> dict:
    """Assemble the system message: prompt + stored user facts."""
    return {"role": "system", "content": build_system_prompt(load_user_info())}


def call_primary_model():
    """Send system prompt, recent conversation, and tool schemas to the model.

    Only the last MAX_MESSAGES messages are sent to keep requests fast.
    """
    recent = conversation[-MAX_MESSAGES:] if MAX_MESSAGES else conversation
    if SWAP_MODELS:
        # Free memory held by the advanced model before loading the primary.
        models.unload_others(PRIMARY_MODEL)
    return ollama.chat(
        model=PRIMARY_MODEL,
        messages=[build_system_message(), *recent],
        tools=list(TOOLS.values()),
        options=_model_options(),
        keep_alive=PRIMARY_KEEP_ALIVE,
    )


def run_agent(
    user_input: str,
    on_tool_event=None,
    on_model_event=None,
) -> str:
    """Run one full request: model -> tools -> answer.

    on_tool_event, if given, is called with ("call", name, args) before a tool
    runs and ("result", name, result) after it finishes.

    on_model_event, if given, is called with ("start", model_name) /
    ("end", model_name) around each primary model invocation.
    """
    conversation.append(create_user_message(user_input))

    for _ in range(MAX_TURNS):
        if on_model_event is not None:
            on_model_event("start", PRIMARY_MODEL)
        try:
            response = call_primary_model()
        except Exception as exc:
            # Text-only models reject attached screenshots. Retry without them.
            if "multimodal" in str(exc).lower() and _strip_screenshot_images():
                response = call_primary_model()
            else:
                raise

        if on_model_event is not None:
            on_model_event("end", PRIMARY_MODEL)
        conversation.append(response.message)

        if not response.message.tool_calls:
            reply = response.message.content or ""
            break

        for tool_call in response.message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = dict(tool_call.function.arguments)

            if on_tool_event is not None:
                on_tool_event("call", tool_name, tool_args)

            tool_function = TOOLS.get(tool_name)
            try:
                if tool_function is None:
                    tool_result = (
                        f"unknown tool: {tool_name}. "
                        f"available tools: {', '.join(TOOLS)}"
                    )
                else:
                    tool_result = tool_function(**tool_args)
            except Exception as exc:
                tool_result = f"tool error: {type(exc).__name__}: {exc}"

            tool_message: dict = {
                "role": "tool",
                "tool_name": tool_name,
                "content": str(tool_result),
            }

            image_path = _screenshot_image(tool_name, str(tool_result))
            if image_path is not None:
                tool_message["images"] = [image_path]

            conversation.append(tool_message)

            if on_tool_event is not None:
                on_tool_event("result", tool_name, str(tool_result))
    else:
        reply = (
            f"(stopped after {MAX_TURNS} rounds of tool calls "
            "without a final answer)"
        )

    save_history()
    return reply
