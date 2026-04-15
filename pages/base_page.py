import os
from playwright.sync_api import Page


class BasePage:
    BASE_URL = os.getenv("BASE_URL", "https://www.saucedemo.com")

    def __init__(self, page: Page):
        self.page = page

    def navigate_to(self, path: str = ""):
        self.page.goto(f"{self.BASE_URL}{path}")

    def get_title(self) -> str:
        return self.page.title()

    def wait_for_page_load(self):
        self.page.wait_for_load_state("networkidle")
