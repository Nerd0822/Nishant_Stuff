from utils import ollama_utils
from config import MODELS,MODEL_OPTIONS

def chat(query,history):
    messages = history + [{"role": "user", "content": query}]
    res = ollama_utils.parse_to(
        model=MODELS["chat_model"],
        query=query,
        stream=True,
        keep_alive=0,
        messages=messages,
        options=MODEL_OPTIONS.get("chat_model"),
    )
    return ollama_utils.stream_output(res)