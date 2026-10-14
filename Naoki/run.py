from agent import CONFIG, Naoki
from helper import handle_user_input, show_art, archive
from langchain_core.messages import HumanMessage
from rag import index
from vtube_controller import fire_for_reply


def main():
    show_art()
    bot = Naoki()
    written = len(bot.app.get_state(CONFIG).values.get("messages", []))

    while True:
        try:
            user = input("YOU > ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not handle_user_input(user):
            break
        if not user.strip():
            continue

        print("Naoki > ", end="", flush=True)
        result = None
        try:
            result = bot.app.invoke(
                {"messages": [HumanMessage(content=user.strip())]}, CONFIG
            )
        except KeyboardInterrupt:
            # Ctrl+C mid-generation: abandon this turn, keep the REPL. turn()
            # never returned, so nothing was appended to state.
            print("\n[interrupted]")
            continue
        except Exception as e:
            # A failing tool (bad path, dead URL, IMAP error) otherwise takes
            # the whole REPL down with it.
            print(f"\n[{type(e).__name__}: {e}]")
            continue

        # Fire the matching VTube Studio expression from the reply text.
        # reply_text = ""
        # if isinstance(result, dict) and result.get("messages"):
        #     try:
        #         reply_text = result["messages"][-1].content or ""
        #     except Exception:
        #         reply_text = ""
        # if reply_text:
        #     fired, detail = fire_for_reply(reply_text)
        #     if fired or "error" in detail.lower():
        #         print(f"[VTS: {detail}]")

        written = archive(bot, written, CONFIG)
        try:
            index()
        except Exception as e:
            print(f"[index failed: {type(e).__name__}: {e}]")


if __name__ == "__main__":
    main()
