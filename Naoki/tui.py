"""Rich text-mode interface for Naoki.

Keeps the terminal UI separate from the agent logic in core.py so other
front-ends (voice, GUI, web) can reuse run_agent() without touching core.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

import voice
from core import run_agent
from helper import conversation, load_history, save_history

console = Console()

COMMANDS = (
    "/help  show commands",
    "/clear  start a new session",
    r"/tts \[on|off]  voice output",
    r"/voice \[engine]  switch engine",
    "/exit  quit",
)
COMMANDS_HELP = "   ".join(COMMANDS)


def welcome() -> None:
    console.print(
        Panel.fit(
            "[bold magenta]Naoki[/bold magenta] — local assistant\n"
            f"[dim]{COMMANDS_HELP}[/dim]",
            border_style="magenta",
        )
    )


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
            f"[dim]unknown engine '{choice}' — available: "
            f"{', '.join(voice.ENGINE_NAMES)}[/dim]"
        )
        return
    ready = voice.engine_status().get(choice, False)
    note = "" if ready else " (not installed — flite will speak instead)"
    console.print(f"[dim]engine switched to {choice}{note}[/dim]")


def main() -> None:
    load_history()
    welcome()
    if conversation:
        console.print(f"[dim]restored {len(conversation)} messages from history[/dim]")

    while True:
        try:
            user_text = console.input("[bold cyan]you ❯ [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/dim]")
            break

        if not user_text:
            continue
        if user_text in ("/exit", "/quit", "exit", "quit"):
            console.print("[dim]bye[/dim]")
            break
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
        if user_text.startswith("/"):
            console.print("[dim]unknown command — try /help[/dim]")
            continue

        try:
            with console.status("[dim]naoki is thinking...[/dim]", spinner="dots"):
                reply = run_agent(user_text)
        except KeyboardInterrupt:
            console.print("[dim]cancelled[/dim]")
            continue
        except Exception as exc:
            console.print("[red]error:[/red]", Text(str(exc)))
            continue

        console.print("\n[bold green]naoki ❯[/bold green]")
        console.print(Text(reply or "(no reply)"))
        engine_used = voice.speak(reply)
        if engine_used:
            console.print(Text(f"[voice: {engine_used}]", style="dim"))
        console.print()


if __name__ == "__main__":
    main()
