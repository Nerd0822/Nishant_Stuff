from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def ask_user(question: str) -> str:
    """Ask the user a clarifying question mid-task and wait for their answer.
    Use when the request is ambiguous and guessing would be costly.
    Returns their reply."""
    return str(interrupt({"question": question}))
