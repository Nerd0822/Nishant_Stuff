import json

from config import MEMORY


def check_for_memory():
    if not MEMORY.exists():
        MEMORY.touch()
    if MEMORY.exists() and MEMORY.stat().st_size > 0:
        with open(MEMORY, "r") as f:
            messages = json.load(f)
    else:
        messages = []

    return messages


def save_memory(messages):
    trimmed = messages[-6:]
    with open(MEMORY, "w") as f:
        json.dump(trimmed, f, indent=2)


def build_user_message(user_input):
    return {"role": "user", "content": user_input}


def user_wants_to_quit(user_input: str) -> bool:

    if user_input.lower() in ["exit", "bye", "see you"]:
        output = True
    else:
        output = False

    return output
