import html as html_lib
import re
import urllib.parse
from pathlib import Path

import httpx
from langchain_core.tools import tool

from config import DOWNLOAD_DIR, USER_AGENT, WEB_MAX_RESULTS, WEB_TIMEOUT


def _ddg_unwrap(href: str) -> str:
    try:
        if href.startswith("//"):
            href = "https:" + href
        parsed = urllib.parse.urlparse(href)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            qs = urllib.parse.parse_qs(parsed.query)
            inner = qs.get("uddg", [""])[0]
            if inner:
                return inner
        return href
    except ValueError:
        return href


@tool
def web_search(query: str, max_results: int = WEB_MAX_RESULTS) -> str:
    """Search the web with DuckDuckGo (no API key). Args: query, max_results (1-10). Returns title/url/snippet lines."""
    query = (query or "").strip()
    if not query:
        return "empty query"
    max_results = max(1, min(int(max_results), 10))
    try:
        resp = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=WEB_TIMEOUT,
        )
        resp.raise_for_status()
        page = resp.text
    except (httpx.HTTPError, OSError, ValueError) as e:
        return f"web search error: {type(e).__name__}: {e}"
    try:
        blocks = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>(.*?)'
            r'(?:<a[^>]*class="result__snippet"[^>]*>(.*?)</a>|<div[^>]*class="result__snippet"[^>]*>(.*?)</div>)',
            page,
            re.DOTALL | re.IGNORECASE,
        )
        # Fallback: anchors only if snippet pattern missed
        if not blocks:
            anchors = re.findall(
                r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                page,
                re.DOTALL | re.IGNORECASE,
            )
            blocks = [(h, t, "", "", "") for h, t in anchors]
        out: list[str] = []
        for i, b in enumerate(blocks[:max_results]):
            href, title_html = b[0], b[1]
            snippet_html = next((x for x in b[2:] if x), "")
            url = _ddg_unwrap(html_lib.unescape(href.strip()))
            if url.startswith("/") or "duckduckgo.com" in url:
                continue
            title = html_lib.unescape(re.sub(r"<[^>]+>", "", title_html)).strip()
            snippet = html_lib.unescape(re.sub(r"<[^>]+>", "", snippet_html)).strip()
            out.append(f"{len(out) + 1}. {title}\n{url}\n{snippet}".strip())
        return "\n\n".join(out) if out else "no results"
    except (ValueError, re.error) as e:
        return f"parse error: {type(e).__name__}: {e}"


@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia and return the top article summary. Args: query (article title or topic)."""
    query = (query or "").strip()
    if not query:
        return "empty query"
    try:
        s = httpx.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 5,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=WEB_TIMEOUT,
        )
        s.raise_for_status()
        hits = (s.json().get("query", {}).get("search") or [])
    except (httpx.HTTPError, OSError, ValueError) as e:
        return f"wikipedia search error: {type(e).__name__}: {e}"
    if not hits:
        return "no wikipedia results"
    title = hits[0].get("title", query)
    try:
        r = httpx.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}",
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=WEB_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPError, OSError, ValueError) as e:
        alts = ", ".join(h.get("title", "") for h in hits[1:4])
        return f"summary fetch failed ({type(e).__name__}), top hit: {title}. alternatives: {alts}"
    extract = (data.get("extract") or "")[:2000]
    url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page", "")
    return f"{data.get('title', title)}\n{url}\n{extract}".strip()


@tool
def download_file(url: str, filename: str = "") -> str:
    """Download a file (image, video, or anything else) to ~/Downloads/naoki.
    Args: url, filename (optional; defaults to the name in the URL).
    Overwrites a file of the same name. Returns the saved path and size."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    raw = filename or urllib.parse.urlparse(url).path
    # Path(...).name strips any directory component, so "../x" cannot escape the folder.
    dest = DOWNLOAD_DIR / (Path(raw).name or "download")
    try:
        # stream, never .content — a video would otherwise buffer entirely in memory
        with httpx.stream(
            "GET",
            url,
            follow_redirects=True,
            timeout=httpx.Timeout(WEB_TIMEOUT, read=60.0),
        ) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
    except (httpx.HTTPError, OSError, ValueError) as e:
        return f"download error: {type(e).__name__}: {e}"
    return f"saved {dest} ({dest.stat().st_size} bytes)"
