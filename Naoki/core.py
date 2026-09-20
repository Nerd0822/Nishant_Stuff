import ollama

from config import MAX_TURNS, PRIMARY_MODEL
from helper import conversation, create_user_message, load_user_info, save_history
from prompt import build_system_prompt
from tools import TOOLS


def build_system_message() -> dict:
    """Assemble the system prompt from prompt.py plus stored user facts."""
    return {"role": "system", "content": build_system_prompt(load_user_info())}


def call_primary_model():
    """Send the system prompt, conversation, and tools to the primary model."""
    return ollama.chat(
        model=PRIMARY_MODEL,
        messages=[build_system_message(), *conversation],
        tools=list(TOOLS.values()),  # Ollama converts each function to a JSON schema
    )


def run_agent(user_input: str, on_tool_event=None) -> str:
    """Run one full request: model -> tool calls -> tool results -> answer.

    on_tool_event, when given, is called with ("call", name, args) before a
    tool runs and ("result", name, result_text) after it finishes, so a
    front-end can show what the model is doing. core never prints itself.
    """
    conversation.append(create_user_message(user_input))

    for _ in range(MAX_TURNS):
        response = call_primary_model()
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

            conversation.append(
                {"role": "tool", "tool_name": tool_name, "content": str(tool_result)}
            )
            if on_tool_event is not None:
                on_tool_event("result", tool_name, str(tool_result))
    else:
        reply = (
            f"(stopped after {MAX_TURNS} rounds of tool calls without a final answer)"
        )

    save_history()
    return reply
