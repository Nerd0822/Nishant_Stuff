from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessageChunk, SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from config import MODEL, PERSONA
from tools import TOOLS
from rag import get_retriever

retriever = get_retriever()


class State(MessagesState):
    context: str


tools = TOOLS.values()

AI = ChatOllama(model=MODEL,keep_alive="30m").bind_tools(list(TOOLS.values()))


def retrieve(state: State):
    question = state["messages"][-1].content
    docs = retriever.invoke(question)
    return {"context": "\n\n".join(d.page_content for d in docs)}


def llm(state: MessagesState):
    # Persona first so it outranks the retrieved context below it.
    prefix = [SystemMessage(content=PERSONA)] if PERSONA else []
    if state.get("context"):
        prefix.append(
            SystemMessage(
                content="Relevant past conversations (use only if helpful):\n"
                + state["context"]
            )
        )
    messages = prefix + state["messages"]

    reply = AIMessageChunk(content="")
    for chunk in AI.stream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
        reply += chunk
    print()
    return {"messages": [reply]}


builder = StateGraph(State)

builder.add_node("retrieve", retrieve)
builder.add_node("llm", llm)
builder.add_node("tools", ToolNode(tools))


builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "llm")
builder.add_conditional_edges("llm", tools_condition)
builder.add_edge("tools", "llm")


app = builder.compile(checkpointer=MemorySaver())

# Pass this to invoke/get_state. The checkpointer owns the conversation, so
# callers pass only the new message and the graph supplies everything before it.
CONFIG = {"configurable": {"thread_id": "naoki"}}
