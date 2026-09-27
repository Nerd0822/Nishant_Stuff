from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from config import CHAT_MODEL, SYSTEM_PROMPT
from tools import TOOLS
from vector import search_relevant


@lru_cache(maxsize=1)
def get_model():
    """Lazily built so importing this module does not load the model."""
    return ChatOllama(model=CHAT_MODEL).bind_tools(TOOLS)


def retrieve(state: MessagesState) -> dict:
    """Deterministic step: past-chat RAG. Runs once, before any agent step."""
    question = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            question = m.content if isinstance(m.content, str) else ""
            break
    docs = search_relevant(question) if question else []
    ctx = (
        "\n".join(
            f"[{d.metadata['ts']}] {d.metadata['topic']}: {d.metadata['text']}"
            for d in docs
        )
        or "No past chats...."
    )
    return {
        "messages": [
            SystemMessage(
                content=f"{SYSTEM_PROMPT}\n\nRelevant context from past chats:\n{ctx}",
                id="naoki-system",
            )
        ]
    }


def agent(state: MessagesState) -> dict:
    """Agentic step: model decides to answer or call tools."""
    return {"messages": [get_model().invoke(state["messages"])]}


def should_continue(state: MessagesState) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


builder = StateGraph(MessagesState)
builder.add_node("retrieve", retrieve)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

# MemorySaver = persistence + resume. thread_id picks the conversation.
app = builder.compile(checkpointer=MemorySaver())