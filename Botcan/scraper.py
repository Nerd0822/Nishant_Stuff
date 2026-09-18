from playwright.sync_api import sync_playwright
import yaml
import os
import json
import csv

from logger import Logger




class Scraper:
    def __init__(self):

        self.pw = sync_playwright().start()
        self.logger = Logger.make_logger(
            name=self.__class__.__name__, output="Scraper/output/scraper.log"
        )
        self.extracted_data = {}

    def start(self, mode: bool = False):

        self.browser = self.pw.firefox.launch(headless=mode)

        self.page = self.browser.new_page()

        return self.page

    @staticmethod
    def load_recipe(recipe_path):
        if not os.path.exists(recipe_path):
            raise Exception(
                f"{recipe_path} is not a valid path, or the file does not exist"
            )
        try:
            with open(recipe_path, "r") as f:
                if not f.name.endswith((".yaml", ".yml")):
                    raise Exception(
                        f"{f.name} is not a yaml file only yaml file are supported."
                    )
                recipe = yaml.safe_load(f)
        except Exception as e:
            Logger.make_logger().error(f"Error reading recipe: {e}")
            recipe = None

        return recipe

    def read_recipe(self, recipe):

        for key, value in recipe.items():
            match key:
                case "open":
                    self.page.goto(value, wait_until="networkidle")

                case "close":
                    self.browser.close()
                    self.pw.stop()

                case "steps":
                    self.execute_steps(steps=value)

    def execute_steps(self, steps):
        for step in steps:
            for k, v in step.items():
                self.logger.debug(f"action = {k} - params = {v}")

                locator = self.page.locator(v.get("selector", ""))

                match k:
                    case "click":
                        if v.get("text"):
                            locator = locator.filter(has_text=v.get("text"))
                        locator.click()

                    case "extract":

                        if v.get("all"):
                            data = locator.all_text_contents()
                        elif v.get("first"):
                            data = locator.first.text_content()
                        else:
                            data = locator.text_content()

                        self.extracted_data[v.get("selector")] = data

                    case "fill":
                        locator.fill(v.get("value"))

                    case "screenshot":
                        self.page.screenshot(
                            path=v.get("path"), full_page=v.get("full_page", False)
                        )

                    case "save":
                        path = v.get("path")
                        fmt = v.get("format")
                        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

                        if fmt == "json":
                            with open(path, "w") as f:
                                json.dump(self.extracted_data, f, indent=2)
                        elif fmt == "csv":
                            with open(path, "w", newline="") as f:
                                if self.extracted_data:
                                    writer = csv.DictWriter(
                                        f, fieldnames=self.extracted_data.keys()
                                    )
                                    writer.writeheader()
                                    writer.writerow(self.extracted_data)

                    case "select":
                        locator.select_option(
                            label=v.get("label"),
                            value=v.get("value"),
                            index=v.get("index"),
                        )

                    case "hover":
                        locator.hover()

                    case "wait":
                        if v.get("selector"):
                            self.page.wait_for_selector(
                                v["selector"],
                                timeout=v.get("timeout"),
                                state=v.get("state", "visible"),
                            )
                        elif v.get("timeout"):
                            self.page.wait_for_timeout(v["timeout"])
                        elif v.get("load_state"):
                            self.page.wait_for_load_state(v["load_state"])

                    case "scroll":
                        try:
                            locator.scroll_into_view_if_needed()
                        except Exception as e:
                            self.page.evaluate(
                                f"window.scrollBy(0, {v.get('amount', 20)})"
                            )
                            self.logger.warning(
                                f"Scroll-into-view failed: {e}. Defaulting to scroll by amount {v.get('amount', 20)}"
                            )
