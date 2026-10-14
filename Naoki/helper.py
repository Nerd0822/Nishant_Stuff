from config import MEMORY_DIR
import orjson


def handle_user_input(user: str) -> bool:
    exit_words = ("quit", "exit", "bye")
    return user.strip().lower() not in exit_words


def show_art():
    from config import ART

    print(ART)
    print("Naoki is you personal assistance")


def archive(bot, written: int,CONFIG):
    messages = bot.app.get_state(CONFIG).values["messages"]
    MEMORY_DIR.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_DIR.open("ab") as f:
        for m in messages[written:]:
            if m.type not in ("human", "ai") or not m.content.strip():
                continue
            f.write(orjson.dumps({"role": m.type, "content": m.content}) + b"\n")
    return len(messages)
