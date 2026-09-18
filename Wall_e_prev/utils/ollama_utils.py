import ollama

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
