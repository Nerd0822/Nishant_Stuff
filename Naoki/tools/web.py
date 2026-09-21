"""Web search, DuckDuckGo only.

Deliberately no Google branch: it needs an API key and a CSE ID, which is
setup friction for results that are rarely better for desktop-assistant
questions. DDG's HTML endpoint needs no key; when it rate-limits us the
tool says so instead of returning garbage.
"""

import html
import re
import urllib.parse
import urllib.request

from ._common import _truncate

_HEADERS = {"User-Agent": "NaokiAssistant/0.1 (local desktop assistant)"}


def search_web(query: str) -> str:
    """Search the web, top 5 hits with title, link, snippet.

    Args:
        query: What to search for, e.g. "KDE spectacle screenshot flags".
    """
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    request = urllib.request.Request(
        "https://html.duckduckgo.com/html/", data=data, headers=_HEADERS
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        page = response.read().decode("utf-8", "replace")

    links = re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.DOTALL
    )
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page, re.DOTALL)
    if not links:
        return "no results -- DuckDuckGo is probably rate-limiting us, try again in a bit"

    lines = []
    for index, (href, raw_title) in enumerate(links[:5], 1):
        # DDG wraps outbound links in a redirect; unwrap to the real target.
        target = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get(
            "uddg", [href]
        )[0]
        title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()
        snippet = ""
        if index - 1 < len(snippets):
            snippet = html.unescape(re.sub(r"<[^>]+>", "", snippets[index - 1])).strip()
        lines.append(f"{index}. {title}\n   {target}\n   {snippet}")
    return _truncate("\n".join(lines), 3000)
