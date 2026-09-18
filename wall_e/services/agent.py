"""Wall-E conversational agent.

Works two ways:
  1. Standalone in the terminal:  python -m walle.agent   (or the `walle` command, see pyproject.toml)
  2. Imported into another project:  from walle.agent import Agent   (or  from walle import Agent)
"""

import ollama
from rich.console import Console

from config import ART, MODEL, OLLAMA_OPTIONS
from helper import (
    build_user_message,
    check_for_memory,
    save_memory,
    user_wants_to_quit,
)
from tools import ALL_TOOLS, TOOLS

console = Console()


class Agent:
    def __init__(self):
        self.Model = MODEL
        self.Memory = check_for_memory()

    def stream_response(self, response):
        final_content = ""
        for chunk in response:
            if chunk.message.thinking:
                console.print(chunk.message.thinking, end="", style="italic dim blue")

            if chunk.message.content:
                console.print(chunk.message.content, end="", style="bold cyan")
                final_content += chunk.message.content

            if chunk.message.tool_calls:
                self.Memory.append(chunk.message.model_dump())
                self.check_tool_call(chunk)
                follow_up = self.pass_tool_output_to_model()
                if follow_up:
                    final_content += self.stream_response(follow_up)
                    return final_content

        console.print()
        self.Memory.append({"role": "assistant", "content": final_content})
        return final_content

    def check_tool_call(self, chunk):
        for tool in chunk.message.tool_calls:
            if func_to_call := ALL_TOOLS.get(tool.function.name):
                console.print(
                    f"\n[bold yellow]⚙️  Executing {tool.function.name}:[/bold yellow] [dim]{tool.function.arguments}[/dim]"
                )
                result = func_to_call(**tool.function.arguments)
                console.print(f"[bold green]✅ Result:[/bold green] {result}\n")
                self.Memory.append(
                    {
                        "role": "tool",
                        "content": str(result),
                        "tool_name": tool.function.name,
                    }
                )
            else:
                console.print(
                    f"[bold red]❌ Function '{tool.function.name}' not found[/bold red]"
                )

    def pass_tool_output_to_model(self):
        return ollama.chat(
            model=self.Model,
            messages=self.Memory,
            tools=TOOLS,
            options=OLLAMA_OPTIONS,
            think=True,
            stream=True,
        )

    def start(self, user):
        

        self.Memory.append(build_user_message(user))

        return ollama.chat(
            model=self.Model,
            messages=self.Memory,
            tools=TOOLS,
            options=OLLAMA_OPTIONS,
            think=True,
            stream=True,
        )

    def run(self):
        console.print(
            f"[bold blue]{ART}[/bold blue]\n[dim](Type 'exit', 'bye', or 'see you' to quit)[/dim]\n"
        )
        while True:
            console.print("[bold magenta]YOU:[/bold magenta] ", end="")
            user = input()
            response = self.start(user)
            if response is None:
                console.print("[bold yellow]👋 Have a good day![/bold yellow]\n")
                break
            self.stream_response(response=response)
            save_memory(self.Memory)
            console.print()


def main():
    Agent().run()


if __name__ == "__main__":
    main()
