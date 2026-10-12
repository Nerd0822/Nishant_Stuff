"""Naoki's tools, grouped by category.

Implementations live in the category modules (email, files, shell, web); this
package only assembles the TOOLS dict the agent loop advertises to the model.
Add a tool by writing the function in its category module and adding one line
to TOOLS below.
"""

from .email import read_email, search_emails
from .files import create_file, delete_file, read_file, write_file
from .shell import run_command
from .web import download_file, fetch_url, web_search

# Single source of truth for the agent's tools (name -> function). Keys must
# match the function names, because that is the name Ollama advertises to the
# model and the name that comes back in tool_call.function.name.
TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "create_file": create_file,
    "delete_file": delete_file,
    "run_command": run_command,
    "web_search": web_search,
    "fetch_url": fetch_url,
    "download_file": download_file,
    "read_email": read_email,
    "search_emails": search_emails,
}

__all__ = ["TOOLS"]