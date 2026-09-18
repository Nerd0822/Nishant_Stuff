from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from config import MODELS
from core.router import router
from tools.file_tools import file_tools
from tools.shell_tools import shell_tools
from tools.web_tools import web_tools


def agent_router(query, history):
    """Try the LangChain agent first (for tool-using queries),
    fall back to the existing router for chat/plan/code."""

    llm = ChatOllama(
        model=MODELS["chat_model"],
        temperature=0.2
    )

    all_tools = file_tools + web_tools + shell_tools

    agent = create_agent(
        model=llm,
        tools=all_tools,
        system_prompt=(
            "You are a helpful AI assistant. You have access to tools for "
            "reading files, searching the web, scraping websites, and running "
            "shell commands. Use them when the user asks for information that "
            "requires these capabilities. If the user asks a general question "
            "or wants code/planning help, just answer directly without tools."
        )
    )

    # Build the messages list from history + current query
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": query})

    # Invoke the agent
    result = agent.invoke({"messages": messages})

    # Extract the final response
    response_messages = result["messages"]
    final_msg = response_messages[-1]

    # Check if the agent used any tools
    tool_calls = getattr(final_msg, "tool_calls", [])
    if not tool_calls:
        # No tools used — this is a pure chat/plan/code query
        # Fall back to the existing router
        return router(query, history)

    # Tools were used — return the agent's response
    return final_msg.content