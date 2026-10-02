import sys
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command
from ollama._types import ResponseError

from config import (
    DEFAULT_PROJECT,
    STT_ENABLED,
    SYSTEM_PROMPT,
    TTS_ENABLED,
    TTS_VOICE,
)
from graph import app
from speach import listen_once, speak_streaming
from vector import add_chat, bootstrap

DIM, BOLD, CYAN, RESET = "\033[2m", "\033[1m", "\033[36m", "\033[0m"

THINK_OPEN, THINK_CLOSE = "<think>", "</think>"


def _text_of(msg) -> str:
    c = getattr(msg, "content", "")
    if isinstance(c, str):
        return c
    if isinstance(c, list):  # content blocks: [{type: text, text: ...}]
        return "".join(
            b.get("text", "")
            for b in c
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def _reasoning_of(msg) -> str:
    """Thinking arrives differently across langchain-ollama versions — check all."""
    rc = getattr(msg, "reasoning_content", "") or ""
    if not rc:
        kw = getattr(msg, "additional_kwargs", None) or {}
        rc = kw.get("reasoning_content", "") or ""
    return rc if isinstance(rc, str) else ""


def _tool_name_of(msg) -> str:
    name = getattr(msg, "name", None)
    if name:
        return str(name)
    return str(getattr(msg, "tool_call_id", "tool"))


def answer_with_tools(question: str) -> str:
    """Stream thinking + tool activity live. Returns the full answer text.

    Re-enters the graph after an ask_user interrupt. Under stream_mode="messages"
    the interrupt() call ends the stream without raising, so the pending payload
    is read back off the checkpointer instead.
    """
    full: list[str] = []
    printed_args: set[str] = set()
    in_think = False
    open_tool = False

    cfg = {"configurable": {"thread_id": "cli"}}
    state = {
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT, id="naoki-system"),
            HumanMessage(content=question),
        ]
    }

    while True:
        for item in app.stream(state, config=cfg, stream_mode="messages"):
            msg = item[0] if isinstance(item, (tuple, list)) else item
            mtype = getattr(msg, "type", "")

            # ---- tool call streaming: show name + args as they arrive ----
            chunks = getattr(msg, "tool_call_chunks", None) or []
            if chunks:
                for tc in chunks:
                    tid = tc.get("id") or ""
                    tname = tc.get("name") or ""
                    args = tc.get("args") or ""
                    if tname and tid not in printed_args:
                        if open_tool:
                            print()
                        printed_args.add(tid)
                        open_tool = True
                        print(
                            f"{CYAN}[{BOLD}tool{RESET}{CYAN}] {BOLD}{tname}{RESET}", end=""
                        )
                    if args:
                        print(f"{CYAN}{args}{RESET}", end="", flush=True)
                continue

            # ---- tool result: one short line, never the raw dump ----
            if mtype == "tool":
                name = _tool_name_of(msg)
                body = _text_of(msg).strip().replace("\n", " ")
                preview = body[:160] + ("..." if len(body) > 160 else "")
                print(f"{CYAN}[{name} ->] {DIM}{preview}{RESET}")
                open_tool = False
                continue

            # ---- reasoning / thinking tokens, dimmed ----
            rc = _reasoning_of(msg)
            if rc:
                print(f"{DIM}{rc}{RESET}", end="", flush=True)
                continue

            # ---- answer tokens, with <think> tag fallback ----
            text = _text_of(msg)
            while text:
                if not in_think and THINK_OPEN in text:
                    before, _, text = text.partition(THINK_OPEN)
                    if before:
                        print(before, end="", flush=True)
                        full.append(before)
                    in_think = True
                    continue
                if in_think and THINK_CLOSE in text:
                    think, _, text = text.partition(THINK_CLOSE)
                    print(f"{DIM}{think}{RESET}", end="", flush=True)
                    in_think = False
                    continue
                if in_think:
                    print(f"{DIM}{text}{RESET}", end="", flush=True)
                else:
                    print(text, end="", flush=True)
                    full.append(text)
                text = ""

        # ---- ask_user suspended the graph; ask and resume ----
        pending = next(
            (t.interrupts[0].value for t in app.get_state(cfg).tasks if t.interrupts),
            None,
        )
        if not pending:
            break
        asked = pending.get("question") if isinstance(pending, dict) else str(pending)
        if asked:
            if TTS_ENABLED:
                try:
                    speak_streaming(asked, voice=TTS_VOICE)
                except (OSError, ValueError, RuntimeError) as e:
                    print(f"[tts skipped: {type(e).__name__}: {e}]")
            else:
                print(f"{BOLD}ask_user:{RESET} {asked}")
            answer = ask()
            if not answer or not answer.strip():
                answer = "(no answer given)"
        else:
            answer = "(no answer given)"
        state = Command(resume=answer)

    print()
    return "".join(full)


def answer_plain(question: str) -> str:
    """Fallback path: no tools, no graph. Used when the model can't emit valid
    tool-call JSON. Streams the answer so the user isn't left waiting."""
    from langchain_ollama import ChatOllama

    from config import CHAT_MODEL

    model = ChatOllama(model=CHAT_MODEL)
    msgs = [
        SystemMessage(content=SYSTEM_PROMPT, id="naoki-system"),
        HumanMessage(content=question),
    ]
    chunks: list[str] = []
    print(f"{CYAN}[tools disabled for this turn]{RESET}")
    for token in model.stream(msgs):
        rc = _reasoning_of(token)
        if rc:
            print(f"{DIM}{rc}{RESET}", end="", flush=True)
            continue
        text = _text_of(token)
        if text:
            print(text, end="", flush=True)
            chunks.append(text)
    print()
    return "".join(chunks)


def ask() -> str:
    if STT_ENABLED:
        q = listen_once()
        if q:
            print(f"{BOLD}you:{RESET} {q}")
        return q
    return input("ASK: ")


def run() -> None:
    bootstrap()  # embed any chats added since last run (explicit, not on import)
    print(
        f"{BOLD}Naoki{RESET} ready — voice {'on' if STT_ENABLED else 'off'}, "
        f"tts {'on' if TTS_ENABLED else 'off'}. Ctrl+C to exit.\n"
    )

    while True:
        try:
            q = ask()
        except (EOFError, KeyboardInterrupt):
            print("\nbye, Golu.")
            break
        if not q.strip():
            continue
        if q.strip() == "q":
            break

        start_time = time.perf_counter()
        try:
            ans = answer_with_tools(q)
        except KeyboardInterrupt:
            print("\n[interrupted]")
            continue
        except ResponseError as e:
            # Model produced malformed tool-call JSON. Recoverable: retry once
            # without forcing tools, so the user still gets an answer.
            print(f"\n[tool-call error: {e}]")
            try:
                ans = answer_plain(q)
                if ans:
                    print(ans)
            except (ResponseError, OSError, RuntimeError, ValueError) as e2:
                print(f"[model error: {type(e2).__name__}: {e2}]")
                continue
        except (OSError, RuntimeError, ValueError) as e:
            print(f"\n[model error: {type(e).__name__}: {e}]")
            continue

        # Save first, speak second: a TTS failure must never lose the chat.
        rec = {
            "id": str(int(time.time() * 1000)),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "project": DEFAULT_PROJECT,
            "topic": q[:50],
            "summary": f"Q: {q} A: {ans[:200]}",
            "text": f"Q:{q}\nA:{ans}",
        }
        try:
            add_chat(rec)
        except (OSError, ValueError) as e:
            print(f"[memory error: {type(e).__name__}: {e}]")

        if TTS_ENABLED and ans.strip():
            try:
                speak_streaming(ans, voice=TTS_VOICE)
            except (OSError, ValueError, RuntimeError) as e:
                print(f"[tts skipped: {type(e).__name__}: {e}]")

        print(f"{DIM}--- took {time.perf_counter() - start_time:.2f}s ---{RESET}\n")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nbye, Nish.")
        sys.exit(0)
