import html
import json
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import ollama

from config import (
    ADVANCED_KEEP_ALIVE,
    ADVANCED_MODEL,
    COMMAND_TIMEOUT,
    GOOGLE_API_KEY,
    GOOGLE_CSE_ID,
    MAX_TOOL_CHARS,
)
from helper import append_user_info


def _truncate(text: str, limit: int = MAX_TOOL_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated; {len(text) - limit} more characters]"


def read_file(file_path: str) -> str:
    """Read and return the text contents of a file.

    Use this whenever you need to see what is inside a file.

    Args:
        file_path: Absolute path of the file to read.
    """
    with open(file_path, encoding="utf-8") as f:
        return _truncate(f.read())


def write_file(file_path: str, content: str) -> str:
    """Create or overwrite a file with the given text content.

    Use this when the user asks you to save text, notes, or code to a file.
    If the file already exists, the original is backed up before overwriting.

    Args:
        file_path: Absolute path of the file to write.
        content: The complete text content for the file.
    """
    path = Path(file_path)
    if path.is_file():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{timestamp}")
        counter = 1
        while backup_path.exists():
            counter += 1
            backup_path = path.with_name(f"{path.name}.bak-{timestamp}-{counter}")
        shutil.copy2(path, backup_path)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            # Restore the original so a failed write never loses data.
            shutil.copy2(backup_path, path)
            raise
        return (
            f"wrote {len(content)} characters to {file_path} "
            f"(original backed up to {backup_path})"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {len(content)} characters to {file_path}"


def list_directory(directory_path: str) -> str:
    """List the files and subdirectories inside a directory.

    Use this to explore a folder before reading, writing, or running commands.

    Args:
        directory_path: Absolute path of the directory to list.
    """
    entries = sorted(Path(directory_path).iterdir())
    if not entries:
        return f"{directory_path} is empty"
    listing = "\n".join(f"{e.name}/" if e.is_dir() else e.name for e in entries)
    return _truncate(listing)


def find_files(directory_path: str, pattern: str) -> str:
    """Find files whose name matches a glob pattern, searching recursively.

    Use this to locate files when you do not know their exact path.

    Args:
        directory_path: Absolute path of the directory to search in.
        pattern: Glob pattern for file names, for example "*.py" or "config*".
    """
    matches = sorted(
        str(path) for path in Path(directory_path).rglob(pattern) if path.is_file()
    )
    if not matches:
        return f"no files matching '{pattern}' under {directory_path}"
    listing = "\n".join(matches[:50])
    if len(matches) > 50:
        listing += f"\n... and {len(matches) - 50} more"
    return _truncate(listing)


def file_info(file_path: str) -> str:
    """Report whether a path exists and, if so, its type, size and modification time.

    Use this to check a file or folder before reading, writing, or moving it.

    Args:
        file_path: Absolute path of the file or directory to inspect.
    """
    path = Path(file_path)
    if not path.exists():
        return f"{file_path} does not exist"
    kind = "directory" if path.is_dir() else "file"
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    return f"{file_path}: {kind}, {stat.st_size} bytes, modified {modified}"


def copy_file(source: str, destination: str) -> str:
    """Copy a file or directory to a new location.

    Refuses to overwrite an existing file; copy into an existing directory is allowed.

    Args:
        source: Absolute path of the file or directory to copy.
        destination: Absolute path to copy it to.
    """
    if Path(destination).is_file():
        raise FileExistsError(
            f"destination already exists: {destination} -- pick another path"
        )
    if Path(source).is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)
    return f"copied {source} to {destination}"


def move_file(source: str, destination: str) -> str:
    """Move or rename a file or directory.

    Refuses to overwrite an existing file; moving into an existing directory is allowed.

    Args:
        source: Absolute path of the file or directory to move.
        destination: Absolute path to move it to.
    """
    if Path(destination).is_file():
        raise FileExistsError(
            f"destination already exists: {destination} -- pick another path"
        )
    shutil.move(source, destination)
    return f"moved {source} to {destination}"


def make_directory(directory_path: str) -> str:
    """Create a directory, including any missing parent directories.

    Args:
        directory_path: Absolute path of the directory to create.
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)
    return f"directory ready: {directory_path}"


def run_command(command: str) -> str:
    """Run a shell command on this machine and return its output.

    Use this for tasks the other tools cannot do (installed programs, git,
    system information). Commands are killed if they run too long. Prefer
    read-only commands; never run destructive commands unless the user
    explicitly asked for them.

    Args:
        command: The shell command to run, exactly as typed in a terminal.
    """
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=COMMAND_TIMEOUT
    )
    output = f"{result.stdout}{result.stderr}".strip()
    return _truncate(f"exit code {result.returncode}\n{output}", 4000)


_USER_AGENT = {"User-Agent": "NaokiAssistant/0.1 (local desktop assistant)"}


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=_USER_AGENT)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def search_wikipedia(query: str) -> str:
    """Look up a topic on Wikipedia and return a short plain-text summary.

    Use this for factual questions about people, places, history, science and
    similar encyclopedic topics.

    Args:
        query: The topic to look up, for example "Alan Turing".
    """
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": 1,
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "redirects": 1,
            "format": "json",
        }
    )
    payload = _fetch_json(f"https://en.wikipedia.org/w/api.php?{params}")
    pages = payload.get("query", {}).get("pages", {})
    if not pages:
        return f"no Wikipedia results for '{query}'"
    page = next(iter(pages.values()))
    title = page.get("title", query)
    extract = (page.get("extract") or "").strip()
    summary = _truncate(extract, 800) if extract else "(no summary available)"
    url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
    return f"{title}\n{summary}\nSource: {url}"


def search_google(query: str) -> str:
    """Search the web and return the top few results (title, link, snippet).

    Uses the Google Custom Search API when GOOGLE_API_KEY and GOOGLE_CSE_ID
    are set in config.py; without those keys it falls back to DuckDuckGo.

    Args:
        query: What to search for.
    """
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        params = urllib.parse.urlencode(
            {"key": GOOGLE_API_KEY, "cx": GOOGLE_CSE_ID, "q": query, "num": 5}
        )
        payload = _fetch_json(f"https://www.googleapis.com/customsearch/v1?{params}")
        items = payload.get("items", [])
        if not items:
            return f"no results for '{query}'"
        lines = [
            f"{index}. {item['title']}\n   {item['link']}\n   {item.get('snippet', '')}"
            for index, item in enumerate(items, 1)
        ]
        return _truncate("\n".join(lines), 3000)

    return _search_duckduckgo(query)


def _search_duckduckgo(query: str) -> str:
    """Keyless fallback: scrape DuckDuckGo's HTML endpoint for results."""
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    request = urllib.request.Request(
        "https://html.duckduckgo.com/html/", data=data, headers=_USER_AGENT
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        page = response.read().decode("utf-8", "replace")

    links = re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.DOTALL
    )
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page, re.DOTALL)
    if not links:
        return (
            "no results (DuckDuckGo may be rate-limiting automated queries; set "
            "GOOGLE_API_KEY and GOOGLE_CSE_ID in config.py for official Google results)"
        )

    lines = []
    for index, (href, raw_title) in enumerate(links[:5], 1):
        target = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get(
            "uddg", [href]
        )[0]
        title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()
        snippet = ""
        if index - 1 < len(snippets):
            snippet = html.unescape(re.sub(r"<[^>]+>", "", snippets[index - 1])).strip()
        lines.append(f"{index}. {title}\n   {target}\n   {snippet}")
    return _truncate("\n".join(lines), 3000)


def remember_user_info(info: str) -> str:
    """Store one durable fact about the user in their profile.

    Use this when the user shares stable personal details -- their name,
    preferences, goals, projects, or how they like to be answered. Do not
    store small talk, questions, or temporary details.

    Args:
        info: One short sentence describing the fact to remember.
    """
    if append_user_info(info):
        return f"remembered: {info}"
    return f"already known or empty, nothing stored: {info}"


def delegate_to_advanced_model(task: str) -> str:
    """Delegate a difficult task to the advanced model.

    Use this for hard reasoning, careful coding, or long analysis that the
    primary model may get wrong. The advanced model cannot see this
    conversation, so include every relevant detail inside `task`.

    Args:
        task: A complete, self-contained description of the task to solve.
    """
    response = ollama.chat(
        model=ADVANCED_MODEL,
        messages=[{"role": "user", "content": task}],
        think=False,  # return only the final answer, not the thinking trace
        # 0 unloads the model right after answering, freeing RAM for the
        # primary model; raise to seconds/minutes if delegations get frequent.
        keep_alive=ADVANCED_KEEP_ALIVE,
    )
    return response.message.content or ""


# Single source of truth for the agent's tools (name -> function). Add a tool
# by writing the function and adding one line here. Keys must match the
# function names, because that is the name Ollama advertises to the model and
# the name that comes back in tool_call.function.name.
TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_directory": list_directory,
    "find_files": find_files,
    "file_info": file_info,
    "copy_file": copy_file,
    "move_file": move_file,
    "make_directory": make_directory,
    "run_command": run_command,
    "search_wikipedia": search_wikipedia,
    "search_google": search_google,
    "remember_user_info": remember_user_info,
    "delegate_to_advanced_model": delegate_to_advanced_model,
}
assert all(name == fn.__name__ for name, fn in TOOLS.items()), (
    "TOOLS keys must match their function names"
)
