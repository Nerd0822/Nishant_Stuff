import json
import sys

import yaml
from langchain_core.tools import tool

from config import BOTCAN_DIR

sys.path.insert(0, str(BOTCAN_DIR))
from scraper import Scraper  # noqa: E402

DOCS = BOTCAN_DIR / "scraper_docs.md"


@tool
def botcan_recipe_help() -> str:
    """Botcan recipe YAML syntax: every action, its options, and a minimal working
    example. Call this BEFORE writing YAML for botcan_scrape."""
    return DOCS.read_text(encoding="utf-8")


@tool
def botcan_scrape(url: str, recipe_yaml: str = "", selectors: dict | None = None) -> str:
    """Scrape a page headlessly. Args: url, recipe_yaml (YAML string — call
    botcan_recipe_help first; overrides selectors), selectors (css selectors to
    extract; results are keyed by the selector string). Returns extracted data as JSON."""
    recipe = {"open": url}
    if recipe_yaml.strip():
        try:
            parsed = yaml.safe_load(recipe_yaml)
        except yaml.YAMLError as e:
            return f"bad YAML: {e}"
        if not isinstance(parsed, dict):
            return "recipe must be a YAML mapping with top-level keys: open, steps, close"
        recipe = {"open": url, **parsed}
    elif selectors:
        recipe["steps"] = [{"extract": {"selector": s, "all": True}} for s in selectors]

    bot = Scraper()
    try:
        bot.start(mode=True)  # scraper.py:17 — mode=False launches a visible window
        bot.read_recipe(recipe)
        return json.dumps(bot.extracted_data, indent=2)
    finally:
        # scraper.py:52 — a `close:` step already ran these; AttributeError if
        # start() itself threw. Cleanup is best-effort, so swallow everything.
        for closer in ("browser.close", "pw.stop"):
            try:
                obj = bot
                for part in closer.split("."):
                    obj = getattr(obj, part)
                obj()
            except Exception:
                pass
