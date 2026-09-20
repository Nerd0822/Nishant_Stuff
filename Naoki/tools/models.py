"""Model tools: delegating hard work to the advanced local model."""

import ollama

from config import ADVANCED_KEEP_ALIVE, ADVANCED_MODEL


def delegate_to_advanced_model(task: str) -> str:
    """Delegate a difficult task to the advanced model.

    Use this for hard reasoning, careful coding, or long analysis that the
    primary model may get wrong. The advanced model cannot see this
    conversation, so include every relevant detail inside `task`.

    Args:
        task: A complete, self-contained description of the task to solve.
    """
    response = ollama.chat(
        model=ADVANCED_MODEL,
        messages=[{"role": "user", "content": task}],
        think=False,  # return only the final answer, not the thinking trace
        # 0 unloads the model right after answering, freeing RAM for the
        # primary model; raise to seconds/minutes if delegations get frequent.
        keep_alive=ADVANCED_KEEP_ALIVE,
    )
    return response.message.content or ""
