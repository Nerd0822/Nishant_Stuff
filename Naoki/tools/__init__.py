"""Naoki's tools, grouped by category.

The implementations live in the category modules (files, shell, web,
memory, desktop, models); this package only assembles the single TOOLS
dict the agent loop advertises to Ollama. Add a tool by writing the
function in its category module and adding one line to TOOLS below.
"""

from .desktop import clipboard_copy, open_file, take_note
from .files import (
    append_to_file,
    copy_file,
    current_directory,
    file_info,
    find_files,
    list_directory,
    make_directory,
    move_file,
    read_file,
    write_file,
)
from .memory import remember_user_info
from .models import delegate_to_advanced_model
from .shell import run_command, system_info
from .web import search_google, search_wikipedia

# Single source of truth for the agent's tools (name -> function). Keys must
# match the function names, because that is the name Ollama advertises to
# the model and the name that comes back in tool_call.function.name.
TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "append_to_file": append_to_file,
    "list_directory": list_directory,
    "current_directory": current_directory,
    "find_files": find_files,
    "file_info": file_info,
    "copy_file": copy_file,
    "move_file": move_file,
    "make_directory": make_directory,
    "open_file": open_file,
    "clipboard_copy": clipboard_copy,
    "take_note": take_note,
    "run_command": run_command,
    "system_info": system_info,
    "search_wikipedia": search_wikipedia,
    "search_google": search_google,
    "remember_user_info": remember_user_info,
    "delegate_to_advanced_model": delegate_to_advanced_model,
}
assert all(name == fn.__name__ for name, fn in TOOLS.items()), (
    "TOOLS keys must match their function names"
)

__all__ = ["TOOLS"]
