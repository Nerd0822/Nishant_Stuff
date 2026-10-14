from langchain_core.messages import AIMessageChunk, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from config import MODEL, SYSTEM
from rag import get_retriever
from tools import TOOLS

CONFIG = {"configurable": {"thread_id": "naoki"}}


class State(MessagesState):
    # retrieve is the only writer, so the default replace behaviour is fine.
    context: str


retriever = get_retriever()


class Naoki:
    def __init__(self):
        self.naoki = ChatOllama(
            model=MODEL, keep_alive="30m", reasoning=False
        ).bind_tools(list(TOOLS.values()))

        builder = StateGraph(State)
        builder.add_node("retrieve", self.retrieve)
        builder.add_node("naoki", self.turn)
        builder.add_node("tools", ToolNode(list(TOOLS.values())))
        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "naoki")
        builder.add_conditional_edges("naoki", tools_condition)
        builder.add_edge("tools", "naoki")
        self.app = builder.compile(checkpointer=MemorySaver())

    def retrieve(self, state: State):
        docs = retriever.invoke(state["messages"][-1].content)
        return {"context": "\n\n".join(d.page_content for d in docs)}

    def turn(self, state: State):
        prefix = [SystemMessage(content=SYSTEM)]
        if state.get("context"):
            prefix.append(
                SystemMessage(
                    content="Relevant past conversations (use only if helpful):\n"
                    + state["context"]
                )
            )
        messages = prefix + state["messages"][-5:]

        reply = AIMessageChunk(content="")
        for chunk in self.naoki.stream(messages):
            if chunk.content:
                print(chunk.content, end="", flush=True)
            reply += chunk
        print()
        return {"messages": [reply]}
