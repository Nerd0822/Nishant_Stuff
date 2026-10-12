"""Web tools, no API keys."""

from html.parser import HTMLParser
from pathlib import Path

import httpx
from ddgs import DDGS
from langchain_core.tools import tool

from config import DOWNLOADS_DIR, USER_AGENT, WEB_TIMEOUT


class _Text(HTMLParser):
    """Pull visible text out of HTML, dropping script and style bodies."""

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip and d.strip():
            self.out.append(d.strip())


@tool
def web_search(query: str, limit: int = 5) -> str:
    """Search the web and return titles and URLs. Args: query, limit."""
    hits = DDGS().text(query, max_results=limit)
    if not hits:
        return "(no results)"
    return "\n".join(f"{h['title']}\n{h['href']}" for h in hits)


@tool
def fetch_url(url: str, limit: int = 4000) -> str:
    """Fetch a URL and return its readable text, stripped of HTML. Args: url, limit."""
    r = httpx.get(url, timeout=WEB_TIMEOUT, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    p = _Text()
    p.feed(r.text)
    return " ".join(p.out)[:limit]


@tool
def download_file(url: str, filename: str = "") -> str:
    """Download a URL straight into the Downloads folder.

    Use for anything the user asks to save -- a PDF, an image, a zip, a data
    file. fetch_url only returns readable text and throws the bytes away.
    Args: url, filename (optional, defaults to the name in the URL).
    """
    with httpx.stream(
        "GET", url, timeout=WEB_TIMEOUT, follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as r:
        r.raise_for_status()
        # .name strips any directory the model tried to smuggle in, so
        # "../../.bashrc" lands as ".bashrc" inside Downloads.
        name = Path(filename or url.split("?")[0]).name
        dest = DOWNLOADS_DIR / name
        size = 0
        with dest.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
                size += len(chunk)
    return f"downloaded {size} bytes to {dest}"