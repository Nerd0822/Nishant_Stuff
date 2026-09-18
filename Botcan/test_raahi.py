import os
from scraper import Scraper
from pathlib import Path
from logger import Logger



os.makedirs("Scraper/output", exist_ok=True)

logger = Logger.make_logger(name="RaahiTest", output="Scraper/output/raahi_test.log")
logger.info("Starting Raahi web scraper test...")

bot = Scraper()

bot.start(mode=False)

recipe_path = Path(__file__).resolve().parent / "raahi_recipe.yaml"

recipe = bot.load_recipe(recipe_path=recipe_path)

if recipe is not None:
    bot.read_recipe(recipe=recipe)
    logger.info("Raahi scraping completed successfully")
else:
    logger.warning("Raahi scraping aborted — no valid recipe loaded")