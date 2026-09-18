import os
from scraper import Scraper
from pathlib import Path
from logger import Logger





os.makedirs("Scraper/output/",exist_ok=True)

logger = Logger.make_logger(name="Main", output="Scraper/output/scraper.log")

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)
logger.info("Starting web scraper...")

bot = Scraper()

bot.start(mode=False)

recipe_path = Path(__file__).resolve().parent / "demo_recipe.yaml"

recipe = bot.load_recipe(recipe_path=recipe_path)

if recipe is not None:
    bot.read_recipe(recipe=recipe)
    logger.info("Scraping completed successfully")
else:
    logger.warning("Scraping aborted — no valid recipe loaded")


