import requests
from bs4 import BeautifulSoup
from langchain_core.tools import Tool


def web_search_tool(query: str) -> str:
    """Search the web using a simple HTTP request (DuckDuckGo-style fallback).
    For better results, set the TAVILY_API_KEY environment variable."""
    try:
        # Try Tavily first if available
        import os
        api_key = os.environ.get("TAVILY_API_KEY")
        if api_key:
            from tavily import TavilyClient
            client = TavilyClient(api_key=api_key)
            results = client.search(query=query, max_results=5)
            return "\n\n".join(
                f"Title: {r.get('title', 'N/A')}\nURL: {r.get('url', 'N/A')}\nSnippet: {r.get('content', 'N/A')}"
                for r in results.get("results", [])
            )

        # Fallback: use DuckDuckGo-style search via requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for result in soup.select(".result__body")[:5]:
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            if title_el:
                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                results.append(f"Title: {title}\nURL: {link}\nSnippet: {snippet}")

        return "\n\n".join(results) if results else "No results found."

    except Exception as e:
        return f"Search error: {e}"


def web_scrape_tool(url: str) -> str:
    """Fetch and extract the text content from a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Limit to first 8000 characters
        return text[:8000] + ("..." if len(text) > 8000 else "")

    except Exception as e:
        return f"Scrape error: {e}"


web_tools = [
    Tool(
        name="web_search",
        func=web_search_tool,
        description="Search the web for information. Input: a search query string.",
    ),
    Tool(
        name="web_scrape",
        func=web_scrape_tool,
        description="Fetch and extract text content from a URL. Input: a full URL (https://...).",
    ),
]