import ollama
from config import MODELS, MODEL_OPTIONS, ROUTER_TOOLS, system_msg, task


def stream_output(stream):
    output = []
    for chunk in stream:
        if chunk.message.thinking:
            print(chunk.message.thinking, end="", flush=True)
            output.append(chunk.message.thinking)

        elif chunk.message.content:
            print(chunk.message.content, end="", flush=True)
            output.append(chunk.message.content)

    print()
    return "".join(output)


def trim(history, max_turns=12):
    return history[-max_turns * 2 :]


def parse_to(model, query, stream, keep_alive, tools=None, messages=None, options=None):
    return ollama.chat(
        model=model,
        messages=messages,
        stream=stream,
        keep_alive=keep_alive,
        tools=tools,
        options=options,
    )


def chat_mode(query, history):
    messages = history + [{"role": "user", "content": query}]
    res = parse_to(
        model=MODELS["chat_model"],
        query=query,
        stream=True,
        keep_alive=0,
        messages=messages,
        options=MODEL_OPTIONS.get("chat_model"),
    )
    return stream_output(res)


def plan_mode(query, history):
    messages = history + [{"role": "user", "content": query}]
    res = parse_to(
        model=MODELS["plan_model"],
        query=query,
        stream=True,
        keep_alive=0,
        messages=messages,
        options=MODEL_OPTIONS.get("plan_model"),
    )
    return stream_output(res)


def code_mode(query, history):
    messages = history + [{"role": "user", "content": query}]
    res = parse_to(
        model=MODELS["code_model"],
        query=query,
        stream=True,
        keep_alive=0,
        messages=messages,
        options=MODEL_OPTIONS.get("code_model"),
    )
    return stream_output(res)


def router(query, history):
    messages = [system_msg] + history + [{"role": "user", "content": query}]
    response = parse_to(
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
                return chat_mode(query=rephrased, history=history)

            case "planning":
                print("--- [STAGE 1: PLANNING] ---")
                plan_result = plan_mode(query=rephrased, history=history)

                print("\n--- [STAGE 2: CHATTING SUMMARY] ---")
                chat_prompt = f"Summarize and present the following plan clearly:\n\n{plan_result}"
                return chat_mode(query=chat_prompt, history=history)

            case "coding":
                print("--- [STAGE 1: ARCHITECTURAL PLANNING] ---")
                plan_result = plan_mode(query=rephrased, history=history)

                print("\n--- [STAGE 2: CODE IMPLEMENTATION] ---")
                # PRESERVE ORIGINAL REPHRASED QUERY ALONG WITH PLAN
                code_prompt = (
                    f"Requirements & Tasks:\n{rephrased}\n\n"
                    f"Step-by-Step Implementation Strategy:\n{plan_result}\n\n"
                    f"Write complete, working, production-quality code for all requirements listed above."
                )
                code_result = code_mode(query=code_prompt, history=history)

                print("\n--- [STAGE 3: SOLUTION SUMMARY] ---")
                explain_prompt = f"Provide a brief, helpful summary of the implemented code solutions:\n\n{code_result}"
                return chat_mode(query=explain_prompt, history=history)

    content = msg.get("content")
    print(content)
    return content


if __name__ == "__main__":
    history = []

    query = task

    reply = router(query=query, history=history)
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": reply})
    history = trim(history)
    print("\n------finished--------")
