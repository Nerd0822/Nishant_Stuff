from config import system_msg,MODELS,MODEL_OPTIONS,ROUTER_TOOLS
from utils import ollama_utils
from pipelines import chat_pipeline,plan_pipeline,code_pipeline


def router(query, history):
    messages = [system_msg] + history + [{"role": "user", "content": query}]
    response = ollama_utils.parse_to(
        model=MODELS["router_model"],
        query=query,
        stream=False,
        keep_alive=0,
        tools=ROUTER_TOOLS,
        messages=messages,
        options=MODEL_OPTIONS.get("router_model"),
    )

    msg = response["message"]

    if msg.get("tool_calls"):
        tool_call = msg["tool_calls"][0]["function"]
        tool_name = tool_call["name"]
        rephrased = tool_call.get("arguments", {}).get("query", query)

        print(f"[Router chose: {tool_name}]")
        print(f"[Rephrased: {rephrased}]\n")

        match tool_name:
            case "chatting":
                return chat_pipeline.chat(query=rephrased, history=history)

            case "planning":
                return plan_pipeline.execute_plan_pipeline(query=rephrased, history=history)

            case "coding":
                return code_pipeline.execute_code_pipeline(query=rephrased, history=history)

    content = msg.get("content")
    print(content)
    return content
