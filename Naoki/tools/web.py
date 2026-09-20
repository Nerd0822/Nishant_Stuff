"""Web tools: Wikipedia and web search (keyless fallbacks included)."""

import html
import json
import re
import urllib.parse
import urllib.request

from config import GOOGLE_API_KEY, GOOGLE_CSE_ID

from ._common import _truncate

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
