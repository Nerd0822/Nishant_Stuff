"""Rich terminal UI for Naoki. Run with:  naoki   (see ~/.bashrc)

ASCII splash, boot sequence, chat with live tool calls, spoken replies.
Commands: /help /clear /tts /voice /downloads /reindex /status /exit.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import voice
from config import CHAT_MODEL, PRIMARY_MODEL, STT_SECONDS, TUI_TOOL_PREVIEW_CHARS
from graph import build_graph, build_system
from tools import TOOLS

console = Console()

LOGO = [
    r"███╗   ██╗ █████╗  ██████╗ ██╗  ██╗██╗",
    r"████╗  ██║██╔══██╗██╔═══██╗██║ ██╔╝██║",
    r"██╔██╗ ██║███████║██║   ██║█████╔╝ ██║",
    r"██║╚██╗██║██╔══██║██║   ██║██╔═██╗ ██║",
    r"██║ ╚████║██║  ██║╚██████╔╝██║  ██╗██║",
    r"╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝",
]
LOGO_COLORS = ["magenta", "bright_magenta", "cyan", "bright_cyan", "cyan", "magenta"]
TAGLINE = "local assistant -- nothing leaves this machine"

COMMANDS = (
    "/help  show commands",
    "/clear  start a new session",
    r"/tts \[on|off]  voice output",
    r"/voice \[engine]  switch engine",
    "/talk [secs]  speak instead of typing",
    "/downloads  list fetched files",
    "/reindex  rebuild the search index",
    "/status  system status",
    "/exit  quit",
)
COMMANDS_HELP = "   ".join(COMMANDS)


def print_logo() -> None:
    for line, color in zip(LOGO, LOGO_COLORS):
        console.print(f"[{color}]{line}[/{color}]", highlight=False)
    console.print(f"[dim]{TAGLINE}[/dim]\n")


def status_line(session: int) -> str:
    tts = f"voice {voice.TTS_ENGINE} ({'on' if voice.ENABLED else 'off'})"
    return (
        f"[dim]chat {CHAT_MODEL} · tools {PRIMARY_MODEL} · "
        f"{tts} · session-{session}[/dim]"
    )


# ---------- boot checks (warn, never block) ----------

def check_ollama():
    import ollama

    names = [m.model for m in ollama.list().models]
    return True, f"up, {len(names)} models"


def check_primary():
    import ollama

    names = [m.model for m in ollama.list().models]
    ok = any(PRIMARY_MODEL.split(":")[0] in n for n in names)
    return ok, PRIMARY_MODEL if ok else f"{PRIMARY_MODEL} not pulled"


def check_tools():
    return len(TOOLS) >= 20, f"{len(TOOLS)} tools bound"


def check_index():
    from rag import INDEX_DIR, load_retriever

    if not INDEX_DIR.exists():
        return None, "not built -- run /reindex"
    load_retriever().invoke("health check")
    return True, "FAISS index answers"


def check_voice():
    status = voice.engine_status()
    ready = [n for n, ok in status.items() if ok]
    if not ready:
        return None, "no engine -- replies print silently"
    current = voice.TTS_ENGINE if status.get(voice.TTS_ENGINE) else "flite fallback"
    return True, f"{current} (ready: {', '.join(ready)})"


def check_chat():
    import ollama

    names = [m.model for m in ollama.list().models]
    ok = any(CHAT_MODEL.split(":")[0] in n for n in names)
    if ok:
        return True, f"{CHAT_MODEL} handles chit-chat"
    return None, f"{CHAT_MODEL} not pulled -- big model does everything"


CHECKS = [
    ("ollama", check_ollama),
    ("model", check_primary),
    ("chat", check_chat),
    ("tools", check_tools),
    ("memory index", check_index),
    ("voice", check_voice),
]


def boot() -> None:
    """Splash + one-line-per-system boot table."""
    print_logo()
    table = Table(show_header=False, box=None, padding=(0, 2))
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        mark = (
            "[green]ok[/green]"
            if ok is True
            else ("[yellow]warn[/yellow]" if ok is None else "[red]FAIL[/red]")
        )
        table.add_row(mark, f"[bold]{name}[/bold]", f"[dim]{detail}[/dim]")
    console.print(table)
    console.print("[dim]botcan tools verify on first scrape (lazy boot)[/dim]")


# ---------- chat history on disk ----------

_HISTORY_KEEP = 20


def _history_file():
    from config import BASE_DIR

    return BASE_DIR / "history.json"


def load_history() -> tuple[int, list]:
    """Restore (session, [(user, reply)...]). Empty defaults if none."""
    import json

    try:
        data = json.loads(_history_file().read_text(encoding="utf-8"))
        session = int(data.get("session", 1))
        chat = [(str(u), str(r)) for u, r in data.get("chat", [])]
        return session, chat
    except (OSError, ValueError, AttributeError, TypeError):
        return 1, []


def save_history(session: int, chat: list) -> None:
    """Persist session + last exchanges. Best-effort, never raises."""
    import json

    try:
        _history_file().write_text(
            json.dumps(
                {"session": session, "chat": chat[-_HISTORY_KEEP:]},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


# ---------- commands ----------

def handle_tts(argument: str) -> None:
    """`/tts` toggles; `/tts on` and `/tts off` are explicit."""
    choice = argument.removeprefix("/tts").strip().lower()
    if choice == "on":
        voice.set_enabled(True)
    elif choice == "off":
        voice.set_enabled(False)
    elif choice:
        console.print("[dim]usage: /tts | /tts on | /tts off[/dim]")
        return
    else:
        voice.set_enabled(not voice.ENABLED)
    state = "on" if voice.ENABLED else "off"
    console.print(f"[dim]voice output {state} (engine: {voice.TTS_ENGINE})[/dim]")


def handle_voice(argument: str) -> None:
    """`/voice` shows engine status; `/voice <engine>` switches engines live."""
    choice = argument.removeprefix("/voice").strip().lower()
    if not choice:
        status = ", ".join(
            f"{name}: {'ready' if ready else 'not installed'}"
            for name, ready in voice.engine_status().items()
        )
        console.print(f"[dim]current engine: {voice.TTS_ENGINE}   ({status})[/dim]")
        return
    if not voice.set_engine(choice):
        console.print(
            f"[dim]unknown engine '{choice}' -- available: "
            f"{', '.join(voice.ENGINE_NAMES)}[/dim]"
        )
        return
    ready = voice.engine_status().get(choice, False)
    note = "" if ready else " (not installed -- flite will speak instead)"
    console.print(f"[dim]engine switched to {choice}{note}[/dim]")


def handle_downloads() -> None:
    from config import DOWNLOAD_DIR

    try:
        from tools.downloads import list_downloads

        console.print(
            Panel(
                Text(list_downloads()),
                title="downloads",
                subtitle=str(DOWNLOAD_DIR),
                border_style="cyan",
            )
        )
    except Exception as exc:
        console.print(f"[dim]{DOWNLOAD_DIR}: {exc}[/dim]")


def handle_reindex() -> None:
    from rag import build_index

    with console.status("[dim]rebuilding search index...[/dim]", spinner="dots"):
        build_index()
    console.print("[dim]search index rebuilt[/dim]")


def handle_status(session: int) -> None:
    import memory as mem
    from config import DOWNLOAD_DIR

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold]chat[/bold]", CHAT_MODEL)
    table.add_row("[bold]tools[/bold]", f"{PRIMARY_MODEL} ({len(TOOLS)} tools)")
    table.add_row("[bold]session[/bold]", f"session-{session}")
    table.add_row(
        "[bold]voice[/bold]",
        f"{'on' if voice.ENABLED else 'off'} ({voice.TTS_ENGINE})",
    )
    table.add_row("[bold]facts[/bold]", str(len(mem.get_facts())))
    try:
        saved = [p for p in DOWNLOAD_DIR.iterdir() if p.is_file()]
        table.add_row("[bold]downloads[/bold]", f"{len(saved)} files")
    except OSError:
        table.add_row("[bold]downloads[/bold]", "unreadable")
    console.print(Panel(table, title="naoki status", border_style="magenta"))


# ---------- two brains: small talk vs tool work ----------

import re as _re

_EMOJI_RX = _re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE00-\uFE0F"
    "\u200D\u2190-\u21FF\u2300-\u23FF]+"
)


def _strip_emoji(text: str) -> str:
    """Drop emojis the small model emits despite the system prompt.

    Replies are read aloud (engines speak emoji names out loud), so the
    no-emoji rule is enforced in code for the chat path, not just asked.
    """
    text = _re.sub(_EMOJI_RX, "", text)
    text = _re.sub(r"[ \t]{2,}", " ", text).strip()
    # Few-shot leakage: she copies the example labels into her own text
    # ("Naoki: ..." misread as "naomi:"), then speaks them out loud.
    text = _re.sub(r"^(naoki|naomi)\s*:\s*", "", text, flags=_re.IGNORECASE)
    return text.strip()

_ACTION_WORDS = (
    "open", "launch", "start", "close", "quit", "download", "search",
    "find", "screenshot", "install", "run", "play", "save",
    "write", "read", "list", "show", "scrape", "fetch", "delete",
    "move", "copy", "my ", "mine",
)

# Devanagari script goes to the big brain: the 1B chat model garbles
# it beyond what prompting can fix, while ornith writes it cleanly.
# Roman Hinglish stays on the fast brain -- gemma reads it fine and
# answers in English+slang, which is the whole persona anyway.

# Hindi memory questions ("where do I live", "what's my name") need the
# big brain's facts -- the chat brain remembers nothing between turns.
_HINDI_MEMORY_WORDS = (
    "naam", "rehta", "rehti", "rehte", "pasand",
    "yaad", "umar", "kaam", "mera", "meri", "mere",
)


# Name-recall goes to chat (facts are injected there); real actions
# and memory writes still need the big brain's tools.
_NAME_Q = ("name", "names", "nickname", "nicknames", "naam")
_DO = (
    "open", "launch", "start", "close", "quit", "download", "search",
    "find", "screenshot", "install", "run", "play", "remember", "save",
    "write", "read", "list", "show", "scrape", "fetch", "delete",
    "move", "copy",
)


def route(text: str, chat_ready: bool) -> tuple[str, str]:
    """Split (brain, clean_text). 'chat' is small talk, 'big' does tools.

    A leading "!" forces the big model. Long messages, links, file
    paths, memory questions, and action verbs always go big -- the small
    model has no tools and no memory beyond this turn.
    """
    if text.startswith("!"):
        return "big", text[1:].strip()
    if not chat_ready:
        return "big", text
    lowered = f" {text.lower()} "
    if " read " in lowered and any(
        hint in lowered for hint in ("download", "naoki", "notes")
    ):
        return "chat", text  # safe-root reads -- fenced in _run_chat_tool
    if any(f" {w}" in lowered for w in _NAME_Q) and not any(
        f" {verb}" in lowered or lowered.startswith(f"{verb} ")
        for verb in _DO
    ) and "http" not in lowered and "/" not in text:
        return "chat", text  # pure recall -- facts are injected below
    if (
        len(text) > 250
        or "http" in lowered
        or "/" in text
        or any(f" {verb}" in lowered or lowered.startswith(f"{verb} ")
               for verb in _ACTION_WORDS)
        or any(f" {word}" in lowered for word in _HINDI_MEMORY_WORDS)
    ):
        return "big", text
    return "chat", text


# Persona and examples now live in persona.md (loaded via build_system).
# Kept inline here: nothing. This comment marks where _CHAT_STYLE died.


# Roman-Hinglish salad detector: legit replies carry at most one
# Hindi word; broken mirroring sprays particles everywhere. Three or
# more markers means she slipped -- retry her in English.
HINGLISH_SALAD_WORDS = (
    "hai", "ho", "hun", "hoon", "raha", "rahi", "rahe", "hoga",
    "hogi", "honge", "kya", "kaise", "tum", "aap", "mera", "tera",
    "batao", "sunao", "karne", "liye", "mujhe", "tumhe", "mein",
    "bhi", "abhi", "wahi", "hogaya", "chal", "theek",
)


def _is_salad(reply: str) -> bool:
    lowered = f" {reply.lower()} "
    hits = sum(1 for w in HINGLISH_SALAD_WORDS if f" {w}" in lowered)
    return hits >= 3


def _chat_invoke(
    messages: list, timeout: int = 180, tools: list | None = None,
    think: bool = False,
) -> dict:
    """Single chat completion via raw Ollama API (not LangChain).

    Chit-chat runs think=False (Qwen otherwise burns its budget
    pondering and emits empty replies). Tool turns run think=True:
    tool calls ONLY happen while thinking. Neither `/nothink` nor
    LangChain (which drops unknown fields) can control this; the raw
    API takes `"think": true/false`, which can. Returns the raw
    message dict (with possible tool_calls).
    """
    import json
    import urllib.request

    body: dict = {
        "model": CHAT_MODEL,
        "messages": messages,
        "stream": False,
        "think": think,
        "options": {"num_ctx": 2048, "num_predict": 256, "num_thread": 8},
    }
    if tools:
        body["tools"] = tools
    encoded = json.dumps(body).encode()
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=encoded,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read())
    return payload.get("message", {}) or {}


# Read-only (+ remember) tools the chat brain may call. read_file is
# fenced to safe roots (below) -- secrets live elsewhere on this box.
SAFE_CHAT_TOOLS = (
    "inspect_path",
    "list_apps",
    "list_downloads",
    "fetch_webpage",
    "host_info",
    "remember_fact",
    "read_file",
)


def _chat_readable(path: str) -> bool:
    """True when `path` sits inside a secrets-free root the chat brain
    may read: Naoki's own download folder or her own project code."""
    from config import BASE_DIR, DOWNLOAD_DIR

    try:
        resolved = Path(path).expanduser().resolve()
    except OSError:
        return False
    return any(
        resolved == root or root in resolved.parents
        for root in (DOWNLOAD_DIR.resolve(), BASE_DIR.resolve())
    )


def _chat_tool_schemas() -> tuple[list, str]:
    """Ollama specs + a short override paragraph for the system prompt."""
    from tools import TOOLS

    by_name = {t.name: t for t in TOOLS}
    specs, lines = [], []
    for name in SAFE_CHAT_TOOLS:
        tool = by_name.get(name)
        if tool is None:
            continue
        params = getattr(tool, "args", None) or {"type": "object", "properties": {}}
        specs.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": (tool.description or "")[:300],
                    "parameters": params,
                },
            }
        )
        first_line = (tool.description or "").strip().split("\n")[0]
        lines.append(f"- {tool.name}: {first_line}")
    blurb = (
        "YOUR tools -- ONLY these exist for you. Anything else named "
        "anywhere above is NOT available: do not call it, do not "
        "mention it.\n" + "\n".join(lines)
    )
    return specs, blurb


def _run_chat_tool(name: str, args: dict) -> str:
    """Execute one chat-brain tool call. Read-only results, capped.

    read_file is fenced to safe roots: anything outside is refused
    with a reroute, so secrets can never reach the weak model.
    """
    from tools import TOOLS

    if name == "read_file" and not _chat_readable(str((args or {}).get("path", ""))):
        return (
            "refused: that file is outside my readable folders "
            "(Naoki's downloads, her own code). Ask the big brain."
        )
    tool = next((t for t in TOOLS if t.name == name), None)
    if tool is None:
        return f"unknown tool: {name}"
    try:
        result = tool.invoke(dict(args or {}))
    except Exception as exc:
        return f"tool error: {type(exc).__name__}: {exc}"
    text = str(result)
    if len(text) > 2000:
        text = text[:2000] + f"\n... [truncated; {len(text) - 2000} more]"
    return text


def run_chat(text: str, history: list | None = None) -> tuple[str, float]:
    """One fast turn with the small model: personality, no tools.

    Tuned for CPU speed: tiny context, short replies, most threads --
    and thinking disabled (Qwen burns its budget pondering otherwise).
    `history` is [(user, reply), ...] oldest-first, capped to the last
    3 exchanges so she remembers this conversation, not just this turn.
    """
    started = time.monotonic()
    system = build_system(lean=True)
    import memory as _mem

    _facts = _mem.get_facts()
    if _facts:
        # Chat brain has no retrieval -- hand it the few known facts
        # directly so "what is my name" never needs ornith.
        system += "\nKnown facts about him:\n" + "\n".join(f"- {f}" for f in _facts)
    lowered = f" {text.lower()} "
    tool_mode = any(
        f" {w}" in lowered
        for w in (
            "list", "remember", "inspect", "look", "apps", "download",
            "fetch", "specs", "ram", "cpu", "disk", "space", "read",
        )
    )
    if tool_mode:
        # Small models drown: the full 6k persona buries the tool
        # instructions and calls never come. Tool turns get a short
        # system instead -- name, vibe, facts, tools, nothing else.
        system = (
            "You are Naoki, Nishant's playful, dominating girlfriend. "
            "Short replies, no emojis. Call him golu, goli, or nish."
        )
    specs, blurb = _chat_tool_schemas() if tool_mode else ([], "")
    if blurb:
        system += "\n\n" + blurb
    messages = [{"role": "system", "content": system}]
    for past_user, past_reply in (history or [])[-3:]:
        messages.append({"role": "user", "content": past_user})
        messages.append({"role": "assistant", "content": past_reply})
    messages.append({"role": "user", "content": text})

    def _ask(extra: list | None = None, think: bool = False) -> dict:
        try:
            return _chat_invoke(messages + (extra or []), tools=specs, think=think)
        except Exception:
            return {}

    content = ""
    with console.status("[dim]naoki is thinking...[/dim]", spinner="dots"):
        for _round in range(3):  # model -> tools -> model, at most 3 rounds
            reply = _ask(think=tool_mode and _round == 0)
            calls = reply.get("tool_calls") or []
            content = str(reply.get("content") or "")
            if not calls:
                break
            for call in calls:
                fn = call.get("function", {}) if isinstance(call, dict) else {}
                name = fn.get("name", "?")
                args = fn.get("arguments", {}) or {}
                if isinstance(args, str):
                    import json as _json

                    try:
                        args = _json.loads(args)
                    except ValueError:
                        args = {}
                show_tool_event(name, str(args)[:200], True)
                result = _run_chat_tool(name, args)
                show_tool_event(name, result[:300], False)
                messages.append(
                    {"role": "assistant", "content": content,
                     "tool_calls": [call] if isinstance(call, dict) else []}
                )
                messages.append(
                    {"role": "tool", "content": result}
                )
                content = ""
    if _re.search(r"[\u0900-\u097F]", content) or _is_salad(content):
        # She mirrored into Hindi despite the English-only rule and her
        # Hindi is broken. One corrective retry; English always lands.
        with console.status("[dim]keeping it in English...[/dim]", spinner="dots"):
            try:
                retry = _ask(
                    [{
                        "role": "user",
                        "content": text
                        + "\n\n(Reply in English only. No Hindi, no Devanagari.)",
                    }]
                )
                content = str(retry.get("content") or "") or content
            except Exception:
                pass
    if not content.strip():  # same hiccup as the big model -- one retry
        with console.status("[dim]empty reply -- asking once more...[/dim]",
                            spinner="dots"):
            try:
                content = str(_ask().get("content") or "") or content
            except Exception:
                pass
    return _strip_emoji(str(content)), time.monotonic() - started


def handle_talk(argument: str) -> str | None:
    """`/talk [secs]`: record the mic, transcribe, return the heard text."""
    raw = argument.removeprefix("/talk").strip()
    try:
        seconds = int(raw) if raw else STT_SECONDS
    except ValueError:
        console.print("[dim]usage: /talk [seconds][/dim]")
        return None
    from config import STT_MAX_SECONDS

    seconds = max(1, min(seconds, STT_MAX_SECONDS))
    try:
        with console.status(f"[dim]listening ({seconds}s)...[/dim]", spinner="dots"):
            import stt as _stt

            wav = _stt.record(seconds)
        with console.status("[dim]transcribing...[/dim]", spinner="dots"):
            heard = _stt.transcribe(wav)
        try:
            wav.unlink()
            wav.parent.rmdir()
        except OSError:
            pass
    except RuntimeError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        return None
    console.print(f"[dim]heard: {heard}[/dim]")
    return heard

def show_tool_event(tool_name: str, payload: str, is_call: bool) -> None:
    if is_call:
        console.print(
            f"[dim yellow]>> {tool_name}[/dim yellow]", Text(str(payload)[:200])
        )
    else:
        preview = str(payload)
        if len(preview) > TUI_TOOL_PREVIEW_CHARS:
            preview = (
                preview[:TUI_TOOL_PREVIEW_CHARS]
                + f"\n... [showing first {TUI_TOOL_PREVIEW_CHARS} chars]"
            )
        console.print(f"[dim green]✔ {tool_name}[/dim green]", Text(preview))


def _stream_turn(graph, user_text: str, thread_id: str) -> tuple[str, float, bool]:
    """One streamed pass. Returns (final text, seconds, saw_tool_call)."""
    from langchain_core.messages import HumanMessage

    config = {"configurable": {"thread_id": thread_id}}
    reply = ""
    saw_tools = False
    started = time.monotonic()
    with console.status("[dim]naoki is thinking...[/dim]", spinner="dots"):
        for event in graph.stream(
            {"messages": [HumanMessage(content=user_text)]}, config
        ):
            for _node, update in event.items():
                for message in update.get("messages", []):
                    kind = getattr(message, "type", "?")
                    if kind == "ai":
                        calls = getattr(message, "tool_calls", None) or []
                        if calls:
                            saw_tools = True
                            for call in calls:
                                show_tool_event(
                                    call["name"], str(call.get("args", {})), True
                                )
                        content = getattr(message, "content", "")
                        if content and not calls:
                            reply = _strip_emoji(str(content))
                    elif kind == "tool":
                        show_tool_event(
                            getattr(message, "name", "?"),
                            str(getattr(message, "content", "")),
                            False,
                        )
    return reply, time.monotonic() - started, saw_tools


def _ollama_stop(model: str, wait_secs: int = 0) -> None:
    """Unload one model from RAM. Never raises.

    Unloading 6GB takes minutes on this box, and killing the stop
    client aborts the unload server-side -- so callers choose: block
    generously (freeing room BEFORE a big turn) or fire-and-forget
    (after it, via a detached process the TUI never waits on).
    """
    import shutil
    import subprocess

    if shutil.which("ollama") is None:
        return
    try:
        if wait_secs > 0:
            subprocess.run(
                ["ollama", "stop", model],
                capture_output=True,
                timeout=wait_secs,
            )
        else:
            subprocess.Popen(
                ["ollama", "stop", model],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
    except Exception:
        pass  # worst case it unloads on ollama's own timer


def _unload_primary(force: bool = False) -> None:
    """Drop the 9B model from RAM the moment its turn is done.

    Box has 14GB and ornith eats 6.2GB -- keeping it resident after a
    turn starves everything else. Ollama reloads it on demand next big
    turn (cold cost accepted). force=True is the Ctrl+C path: gracefully
    stopping takes minutes, so also SIGTERM ornith's runner directly.
    ornith is the only model with a vision projector, so matching
    'mmproj' hits exactly its process and nothing else.
    """
    _ollama_stop(PRIMARY_MODEL)
    if force:
        import shutil
        import subprocess

        if shutil.which("pkill") is not None:
            try:
                subprocess.run(
                    ["pkill", "-f", "mmproj"],
                    capture_output=True,
                    timeout=10,
                )
            except Exception:
                pass


def _preload_chat() -> None:
    """Load the small chat model back after a big turn, so chit-chat
    stays instant. Blank prompt = load only, no real generation."""
    import json
    import urllib.request

    from config import CHAT_MODEL as _cm

    try:
        body = json.dumps(
            {"model": _cm, "prompt": " ", "keep_alive": "30m", "stream": False}
        ).encode()
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            response.read()
    except Exception:
        pass  # non-fatal: next chat turn cold-loads instead


def run_turn(graph, user_text: str, thread_id: str) -> tuple[str, float]:
    """Stream one turn: live tool calls, then (final text, seconds).

    Memory juggling for a 14GB box: the chat model is unloaded FIRST so
    ornith has maximum room to reason; on the way out ornith is dropped
    and the chat model preloaded again. The local model sometimes comes
    back empty (no text, no tool call) -- when that happens with nothing
    attempted, retry once before giving up.
    """
    from config import CHAT_MODEL as _cm

    _ollama_stop(_cm, wait_secs=90)  # blocking: room for the big brain
    try:
        reply, seconds, saw_tools = _stream_turn(graph, user_text, thread_id)
        if not reply.strip() and not saw_tools:
            console.print("[dim]empty reply -- asking once more...[/dim]")
            retry, extra, _ = _stream_turn(graph, user_text, thread_id)
            reply, seconds = retry or reply, seconds + extra
        return reply, seconds
    finally:
        _unload_primary()
        _preload_chat()


def main() -> None:
    boot()
    console.print(status_line(1))
    console.print(f"[dim]{COMMANDS_HELP}[/dim]")
    console.print("[dim]prefix a message with ! to force the big model[/dim]\n")
    import ollama

    chat_ready = any(
        CHAT_MODEL.split(":")[0] in m.model for m in ollama.list().models
    )
    if not chat_ready:
        console.print(
            f"[yellow]warn: {CHAT_MODEL} not pulled -- big model does everything[/yellow]"
        )
    graph = build_graph()
    session, chat_history = load_history()
    if chat_history:
        console.print(
            f"[dim]restored {len(chat_history)} past chats (session-{session})[/dim]"
        )

    while True:
        try:
            user_text = console.input("[bold cyan]you ❯ [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/dim]")
            break

        if not user_text:
            continue
        if user_text in ("/exit", "/quit", "exit", "quit"):
            console.print("\n[bold magenta]bye[/bold magenta]")
            break
        if user_text == "/help":
            console.print(f"[dim]{COMMANDS_HELP}[/dim]")
            continue
        if user_text == "/clear":
            session += 1
            chat_history = []
            save_history(session, chat_history)
            console.print(status_line(session))
            console.print("[dim]fresh session -- memory kept, chat reset[/dim]")
            continue
        if user_text == "/tts" or user_text.startswith("/tts "):
            handle_tts(user_text)
            continue
        if user_text == "/voice" or user_text.startswith("/voice "):
            handle_voice(user_text)
            continue
        if user_text == "/talk" or user_text.startswith("/talk "):
            heard = handle_talk(user_text)
            if heard:
                user_text = heard
            else:
                continue
        if user_text == "/downloads":
            handle_downloads()
            continue
        if user_text == "/reindex":
            handle_reindex()
            continue
        if user_text == "/status":
            handle_status(session)
            continue
        if user_text.startswith("/"):
            console.print("[dim]unknown command -- try /help[/dim]")
            continue

        brain, clean = route(user_text, chat_ready)
        try:
            if brain == "chat":
                reply, seconds = run_chat(clean, chat_history)
                chat_history.append((clean, reply))
                save_history(session, chat_history)
            else:
                reply, seconds = run_turn(graph, clean, f"session-{session}")
                console.print("[dim]room shuffled: ornith out, chat model back in[/dim]")
        except KeyboardInterrupt:
            _unload_primary(force=True)
            console.print("[dim]cancelled -- big model killed, RAM freed[/dim]")
            continue
        except Exception as exc:
            console.print("[red]error:[/red]", Text(f"{type(exc).__name__}: {exc}"))
            continue

        tag = CHAT_MODEL.split(":")[0] if brain == "chat" else "ornith"
        console.print(
            Panel(
                Text(reply or "(no reply -- the model came back empty, try again)"),
                title="[bold green]naoki[/bold green]",
                subtitle=f"[dim]{seconds:.1f}s · {tag}[/dim]",
                border_style="green",
            )
        )
        engine_used = voice.speak(reply)
        if engine_used:
            console.print(f"[dim] [voice: {engine_used}][/dim]")
        console.print()

    _ollama_stop(CHAT_MODEL, wait_secs=60)
    console.print("[dim]chat model unloaded -- memory clear[/dim]")


if __name__ == "__main__":
    main()
