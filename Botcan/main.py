import os
from scraper import Scraper
from pathlib import Path


os.makedirs("Scraper/output/",exist_ok=True)

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)
print("Starting web scraper...")

bot = Scraper()

bot.start(mode=False)

recipe_path = Path(__file__).resolve().parent / "test" / "demo_recipe.yaml"

recipe = bot.load_recipe(recipe_path=recipe_path)

if recipe is not None:
    bot.read_recipe(recipe=recipe)
    print("Scraping completed successfully")
else:
    print("Scraping aborted — no valid recipe loaded")
