"""Drive Botcan (the recipe scraper) through its MCP server.

Botcan lives next door (../Botcan/mcp_server.py) and speaks MCP over
stdio. Each wrapper below spawns it fresh per call -- the server is
stateless (fresh headless Firefox every tool call), so no daemon to
manage and nothing to leak. Schemas stay static here on purpose: a 9B
local model picks reliably between fixed tools, not dynamic ones.
"""

import asyncio
import sys
from pathlib import Path

BOTCAN_SERVER = Path(__file__).resolve().parent.parent.parent / "Botcan" / "mcp_server.py"

_TEXT_TIMEOUT = 120
_RECIPE_TIMEOUT = 240


def _call_mcp(tool_name: str, arguments: dict, timeout: int) -> str:
    """Spawn the Botcan MCP server, call one tool, return its text."""
    if not BOTCAN_SERVER.is_file():
        return (
            f"Botcan MCP server not found at {BOTCAN_SERVER} -- "
            "the Botcan project must sit next to Naoki"
        )
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def _run() -> str:
        params = StdioServerParameters(
            command=sys.executable, args=[str(BOTCAN_SERVER)]
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    tool_name, arguments, read_timeout_seconds=timeout
                )
        parts = [
            getattr(block, "text", "") for block in result.content or []
        ]
        text = "".join(parts).strip()
        if getattr(result, "isError", False):
            return f"Botcan reported an error: {text or 'unknown error'}"
        return text or "(Botcan returned no text)"

    return asyncio.run(_run())


def botcan_scrape(url: str) -> str:
    """Scrape a JavaScript-heavy page Botcan-style, return its visible text.

    Use when fetch_webpage returns junk or the page renders in a browser
    (click-to-load content, SPAs). Loads the URL in headless Firefox and
    reads the rendered body -- slower than fetch_webpage, so try that
    first. For multi-step flows (logins, forms, clicking through tabs),
    write a recipe and call botcan_run_recipe instead.

    Args:
        url: Full http(s) link of the page to scrape.
    """
    return _call_mcp("scrape_text", {"url": url}, _TEXT_TIMEOUT)


def botcan_run_recipe(recipe_yaml: str) -> str:
    """Run a Botcan YAML recipe: click, fill, extract across many steps.

    Use for anything fetch_webpage and botcan_scrape can't do alone --
    tab navigation, form fills, hover reveals, screenshots mid-flow. The
    recipe is YAML text with `open: <url>`, `steps:` (click / fill /
    select / hover / scroll / wait / extract / screenshot / save), and
    `close:`. Returns the extracted data as JSON. See Botcan/README.md
    for the full action reference.

    Args:
        recipe_yaml: Complete recipe as YAML text, e.g.
            "open: https://example.com\\nsteps:\\n  - extract:\\n      selector: h1\\nclose:\\n".
    """
    return _call_mcp("run_recipe", {"recipe_yaml": recipe_yaml}, _RECIPE_TIMEOUT)


def botcan_screenshot(url: str) -> str:
    """Capture a full-page browser screenshot of a URL, return its path.

    Use when the user wants to SEE a rendered page (Naoki's own vision
    can then read it), or as proof of what a page looked like. Saved
    under Botcan/output -- pass the path to launch_file to show it.

    Args:
        url: Full http(s) link of the page to capture.
    """
    return _call_mcp("scrape_screenshot", {"url": url}, _TEXT_TIMEOUT)
