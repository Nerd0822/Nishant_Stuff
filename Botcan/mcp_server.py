"""Botcan as an MCP server (stdio transport).

Exposes the Playwright recipe scraper to MCP clients -- Naoki calls it
to drive real browser scraping. Run directly to serve over stdio:

    ../ml_shit/bin/python mcp_server.py

Tools:
- run_recipe: execute a recipe (YAML text) headless, get extracted data.
- scrape_text: quick no-recipe text grab from any http(s) URL.
- scrape_screenshot: full-page PNG of any http(s) URL, returns its path.

Each call launches a fresh headless Firefox and always closes it, so the
server is stateless and safe to spawn per request. stdout is reserved for
the MCP protocol -- logs go to files only.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)  # scraper.py/logger.py use relative output paths
sys.path.insert(0, str(HERE))

os.makedirs("Scraper/output", exist_ok=True)
os.makedirs("output", exist_ok=True)

from mcp.server.mcpserver import MCPServer  # noqa: E402

mcp = MCPServer(
    "botcan",
    description="Headless Firefox web scraper: recipe-driven extraction, quick text grabs, screenshots.",
)

_MAX_TEXT = 6000


def _run_in_browser(work) -> str:
    """Launch headless Firefox, run `work(page)->str`, always clean up."""
    from scraper import Scraper

    bot = Scraper()
    try:
        bot.start(mode=True)  # headless=True: no display needed
        bot.page.set_default_timeout(30000)
        return work(bot)
    finally:
        try:
            bot.browser.close()
        except Exception:
            pass
        try:
            bot.pw.stop()
        except Exception:
            pass


def _truncate(text: str, limit: int = _MAX_TEXT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated; {len(text) - limit} more characters]"


@mcp.tool()
def run_recipe(recipe_yaml: str) -> str:
    """Run a Botcan scraping recipe (YAML text) in headless Firefox.

    A recipe has `open: <url>`, `steps:` (click/fill/extract/screenshot/
    save/wait/scroll/select/hover), and `close:`. Returns the extracted
    data as JSON plus any files the recipe saved.
    """
    import yaml

    try:
        recipe = yaml.safe_load(recipe_yaml)
    except Exception as exc:
        return f"invalid YAML: {type(exc).__name__}: {exc}"
    if not isinstance(recipe, dict) or not ("open" in recipe or "steps" in recipe):
        return "recipe must be a YAML mapping with 'open:' and/or 'steps:' -- see README.md"

    def work(bot) -> str:
        bot.read_recipe(recipe=recipe)
        data = json.dumps(bot.extracted_data, indent=2, ensure_ascii=False)
        saved = sorted(
            str(p) for p in Path("output").glob("*") if p.is_file()
        ) + sorted(str(p) for p in Path("Scraper/output").glob("*") if p.is_file())
        note = f"\nfiles in output dirs: {', '.join(saved[-5:])}" if saved else ""
        return _truncate(f"extracted data:\n{data}{note}")

    try:
        return _run_in_browser(work)
    except Exception as exc:
        return f"recipe run failed ({type(exc).__name__}: {exc})"


@mcp.tool()
def scrape_text(url: str) -> str:
    """Grab the visible text of a web page (no recipe needed).

    Loads the URL in headless Firefox (so JavaScript pages work) and
    returns the rendered body text. For link/file downloads use a
    downloader instead; for clicking through multi-step flows use
    run_recipe with a YAML recipe.
    """
    if not url.startswith(("http://", "https://")):
        return "only http(s) URLs -- paste the full link"

    def work(bot) -> str:
        bot.page.goto(url, wait_until="domcontentloaded")
        text = bot.page.locator("body").inner_text()
        title = bot.page.title()
        head = f"{title}\nSource: {url}\n\n" if title else f"Source: {url}\n\n"
        return _truncate(head + (text or "").strip() or "(page has no readable text)")

    try:
        return _run_in_browser(work)
    except Exception as exc:
        return f"scrape failed ({type(exc).__name__}: {exc})"


@mcp.tool()
def scrape_screenshot(url: str) -> str:
    """Capture a full-page screenshot of a URL, return the PNG path."""
    if not url.startswith(("http://", "https://")):
        return "only http(s) URLs -- paste the full link"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = HERE / "output" / f"botcan-{stamp}.png"

    def work(bot) -> str:
        bot.page.goto(url, wait_until="domcontentloaded")
        bot.page.screenshot(path=str(dest), full_page=True)
        kb = dest.stat().st_size // 1024
        return f"[screenshot: {dest}] saved ({kb} KB)"

    try:
        return _run_in_browser(work)
    except Exception as exc:
        return f"screenshot failed ({type(exc).__name__}: {exc})"


if __name__ == "__main__":
    mcp.run()
