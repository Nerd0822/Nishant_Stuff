import re
from pathlib import Path

import ollama

from config import (
    MAX_MESSAGES,
    MAX_NUM_CTX,
    MAX_PREDICT_TOKENS,
    MAX_TURNS,
    PRIMARY_MODEL,
)
from helper import conversation, create_user_message, load_user_info, save_history
from prompt import build_system_prompt
from tools import TOOLS

_SCREENSHOT_MARKER = re.compile(r"\[screenshot: (.+?)\]")


def _screenshot_image(tool_name: str, result_text: str) -> str | None:
    """Return the screenshot file path if this result carries one."""
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
        # ollama Message objects are mutable pydantic models.
        if not isinstance(message, dict) and hasattr(message, "images"):
            try:
                message.images = None
            except Exception:
                pass
    return removed


def _model_options() -> dict:
    """Build the Ollama options dict from config.

    num_predict caps the output length (fewer generated tokens = faster
    replies). num_ctx optionally shrinks the model's working context window.
    Both are additive: truncating the message list (MAX_MESSAGES) is the
    primary lever for keeping requests fast.
    """
    opts = {"num_predict": MAX_PREDICT_TOKENS}
    if MAX_NUM_CTX is not None:
        opts["num_ctx"] = MAX_NUM_CTX
    return opts


def build_system_message() -> dict:
    """Assemble the system prompt from prompt.py plus stored user facts."""
    return {"role": "system", "content": build_system_prompt(load_user_info())}


def call_primary_model():
    """Send the system prompt, conversation, and tools to the primary model.

    Only the last MAX_MESSAGES messages of the conversation are sent, keeping
    the request small (and fast) regardless of how long the session has run.
    The full conversation is still persisted to history.json.
    """
    recent = conversation[-MAX_MESSAGES:] if MAX_MESSAGES else conversation
    return ollama.chat(
        model=PRIMARY_MODEL,
        messages=[build_system_message(), *recent],
        tools=list(TOOLS.values()),  # Ollama converts each function to a JSON schema
        options=_model_options(),
    )


def run_agent(user_input: str, on_tool_event=None) -> str:
    """Run one full request: model -> tool calls -> tool results -> answer.

    on_tool_event, when given, is called with ("call", name, args) before a
    tool runs and ("result", name, result_text) after it finishes, so a
    front-end can show what the model is doing. core never prints itself.
    """
    conversation.append(create_user_message(user_input))

    for _ in range(MAX_TURNS):
        try:
            response = call_primary_model()
        except Exception as exc:
            # Text-only models reject attached screenshots (400 multimodal
            # error). Retry the turn without images so the text fallback
            # (path + dimensions) still reaches the model.
            if "multimodal" in str(exc).lower() and _strip_screenshot_images():
                response = call_primary_model()
            else:
                raise
        # Keep the assistant turn (it carries the tool calls) before the results.
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
                # Feed the error back as the tool result so the model can
                # correct itself instead of crashing the agent.
                tool_result = f"tool error: {type(exc).__name__}: {exc}"

            tool_message: dict = {
                "role": "tool",
                "tool_name": tool_name,
                "content": str(tool_result),
            }
            # Attach pixels for vision-capable models; text-only models
            # trigger the multimodal retry above and continue text-only.
            image_path = _screenshot_image(tool_name, str(tool_result))
            if image_path is not None:
                tool_message["images"] = [image_path]
            conversation.append(tool_message)
            if on_tool_event is not None:
                on_tool_event("result", tool_name, str(tool_result))
    else:
        reply = (
            f"(stopped after {MAX_TURNS} rounds of tool calls without a final answer)"
        )

    save_history()
    return reply
