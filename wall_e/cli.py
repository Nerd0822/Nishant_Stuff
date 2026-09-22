"""Terminal interface for the assistant.

Kept separate from the agent logic in agent.py so other front-ends (tts, GUI)
can reuse run_agent() without touching the CLI code.
"""

import atexit
import signal

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import models, tts
from .agent import run_agent
from .config import ADVANCED_MODEL, PRIMARY_MODEL, TUI_TOOL_PREVIEW_CHARS
from .conversation import conversation, load_history, save_history

console = Console()

COMMANDS = (
    "/help  show commands",
    "/clear  start a new session",
    r"/tts [on|off]  voice output",
    r"/voice [name]  show or switch voice",
    "/models  show models in memory",
    "/unload  free model memory",
    "/exit  quit",
)
COMMANDS_HELP = "   ".join(COMMANDS)


def welcome() -> None:
    console.print(
        Panel.fit(
            "[bold magenta]Wall-e[/bold magenta] — local assistant\n"
            f"[dim]{COMMANDS_HELP}[/dim]",
            border_style="magenta",
        )
    )


def unload_models(announce: bool = True) -> None:
    """Evict every loaded model (used by /unload, exit, and SIGTERM)."""
    loaded = models.loaded_models()
    if loaded and announce:
        console.print(f"[dim]unloading: {', '.join(loaded)}[/dim]")
    models.unload_all()
    tts.shutdown()  # the kokoro weights sit in RAM too


def handle_tts(argument: str) -> None:
    """`/tts` toggles; `/tts on` and `/tts off` are explicit."""
    choice = argument.removeprefix("/tts").strip().lower()
    if choice == "on":
        tts.set_enabled(True)
    elif choice == "off":
        tts.set_enabled(False)
    elif choice:
        console.print("[dim]usage: /tts | /tts on | /tts off[/dim]")
        return
    else:
        tts.set_enabled(not tts.ENABLED)
    state = "on" if tts.ENABLED else "off"
    console.print(f"[dim]voice output {state} (voice: {tts.VOICE})[/dim]")


def handle_voice(argument: str) -> None:
    """`/voice` shows the audio stack; `/voice <name>` switches voice live."""
    choice = argument.removeprefix("/voice").strip().lower()
    if not choice:
        console.print(
            f"[dim]voice: {tts.VOICE}   speed: {tts.TTS_SPEED}   "
            f"realtime: {tts.TTS_REALTIME}[/dim]"
        )
        status = "   ".join(
            f"{name}: {'ok' if ready else 'missing'}"
            for name, ready in tts.voice_status().items()
        )
        console.print(f"[dim]{status}[/dim]")
        voices = tts.available_voices()
        if voices:
            console.print(f"[dim]{len(voices)} voices: {' '.join(voices)}[/dim]")
        return
    if not tts.set_voice(choice):
        voices = tts.available_voices()
        listing = " ".join(voices) if voices else "af_nicole, af_heart, ..."
        console.print(f"[dim]unknown voice '{choice}' — available: {listing}[/dim]")
        return
    console.print(f"[dim]voice switched to {tts.VOICE}[/dim]")


def handle_models() -> None:
    """`/models` lists what Ollama currently holds in memory."""
    loaded = models.loaded_models()
    if not loaded:
        console.print("[dim]no models loaded[/dim]")
        return
    roles = {PRIMARY_MODEL: "primary", ADVANCED_MODEL: "advanced"}
    for name in loaded:
        role = roles.get(name)
        suffix = f"  ({role})" if role else ""
        console.print(f"[dim]{name}{suffix}[/dim]")


def handle_unload() -> None:
    """`/unload` frees model memory now."""
    if not models.loaded_models():
        console.print("[dim]no models loaded[/dim]")
        return
    unload_models()


def show_model_event(kind: str, model_name: str) -> None:
    """Print which model is generating the current reply."""
    if kind == "start":
        console.print(f"[dim cyan]🤖 {model_name}[/dim cyan]")


def show_tool_event(kind: str, tool_name: str, payload) -> None:
    """Print tool calls and results as they happen."""
    if kind == "call":
        if tool_name == "ask_expert":
            console.print(f"[dim cyan]🤖 → {ADVANCED_MODEL} (delegated)[/dim cyan]")
        console.print(f"[dim yellow]⚙ {tool_name}[/dim yellow]", Text(str(payload)))
        return
    preview = str(payload)
    if len(preview) > TUI_TOOL_PREVIEW_CHARS:
        preview = (
            preview[:TUI_TOOL_PREVIEW_CHARS]
            + f"\n... [showing first {TUI_TOOL_PREVIEW_CHARS} chars]"
        )
    console.print(f"[dim green]✔ {tool_name}[/dim green]", Text(preview))


def chat_loop() -> None:
    while True:
        try:
            user_text = console.input("[bold cyan]you ❯ [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/dim]")
            return

        if not user_text:
            continue
        if user_text in ("/exit", "/quit", "exit", "quit"):
            console.print("[dim]bye[/dim]")
            return
        if user_text == "/help":
            console.print(f"[dim]{COMMANDS_HELP}[/dim]")
            continue
        if user_text == "/clear":
            conversation.clear()
            save_history()
            console.print("[dim]conversation cleared[/dim]")
            continue
        if user_text == "/tts" or user_text.startswith("/tts "):
            handle_tts(user_text)
            continue
        if user_text == "/voice" or user_text.startswith("/voice "):
            handle_voice(user_text)
            continue
        if user_text == "/models":
            handle_models()
            continue
        if user_text == "/unload":
            handle_unload()
            continue
        if user_text.startswith("/"):
            console.print("[dim]unknown command — try /help[/dim]")
            continue

        history_len = len(conversation)
        try:
            with console.status("[dim]wall-e is thinking...[/dim]", spinner="dots"):
                reply = run_agent(
                    user_text,
                    on_tool_event=show_tool_event,
                    on_model_event=show_model_event,
                )
        except KeyboardInterrupt:
            # Drop everything the cancelled turn added, so it leaves no trace.
            del conversation[history_len:]
            console.print("[dim]cancelled[/dim]")
            continue
        except Exception as exc:
            console.print("[red]error:[/red]", Text(str(exc)))
            continue

        console.print("\n[bold green]wall-e ❯[/bold green]")
        console.print(Text(reply or "(no reply)"))
        try:
            spoke = tts.speak(reply)
        except KeyboardInterrupt:
            # The reply is already in history; only the audio was cancelled.
            tts.stop()
            console.print(Text("[voice: stopped]", style="dim"))
        else:
            if spoke:
                console.print(Text(f"[voice: {tts.VOICE}]", style="dim"))
        console.print()


def _on_sigterm(signum, frame) -> None:
    """Exit promptly; main()'s finally block unloads every model."""
    raise SystemExit(0)


def main() -> None:
    load_history()
    welcome()
    if conversation:
        console.print(f"[dim]restored {len(conversation)} messages from history[/dim]")

    signal.signal(signal.SIGTERM, _on_sigterm)
    atexit.register(unload_models, announce=False)
    try:
        chat_loop()
    finally:
        unload_models()


if __name__ == "__main__":
    main()
