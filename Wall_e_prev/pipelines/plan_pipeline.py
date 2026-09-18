from utils import ollama_utils
from config import MODELS, MODEL_OPTIONS
from pipelines.chat_pipeline import chat


def plan(query, history):
    messages = history + [{"role": "user", "content": query}]
    res = ollama_utils.parse_to(
        model=MODELS["plan_model"],
        query=query,
        stream=True,
        keep_alive=0,
        messages=messages,
        options=MODEL_OPTIONS.get("plan_model"),
    )
    return ollama_utils.stream_output(res)

def execute_plan_pipeline(query,history):
    print("--- [STAGE 1: PLANNING] ---")
    plan_result = plan(query, history=history)
    print("\n--- [STAGE 2: CHATTING SUMMARY] ---")
    chat_prompt = f"Summarize and present the following plan clearly:\n\n{plan_result}"
    return chat(query=chat_prompt, history=history)
    