import re
import pytest_check as check
from playwright.sync_api import Page
from utils.config import config


class BasePage:
    BASE_URL = config["base_url"]

    def __init__(self, page: Page):
        self.page = page

    def navigate_to(self, path: str = ""):
        self.page.goto(f"{self.BASE_URL}{path}")

    def get_title(self) -> str:
        return self.page.title()

    def wait_for_page_load(self):
        self.page.wait_for_load_state("networkidle")

    def assert_text_has_no_html(self, locator, label: str = "Element"):
        """
        Soft assertion — verifies a locator's text contains no raw HTML tags,
        unescaped entities, or method-call patterns (possible unresolved code).
        Test continues even if any check fails.
        """
        text = locator.inner_text()

        # Check for raw HTML tags
        check.is_not_in("<", text, f"{label} contains raw HTML tag: {text!r}")
        check.is_not_in(">", text, f"{label} contains raw HTML tag: {text!r}")

        # Check for unescaped HTML entities
        check.is_false(
            any(e in text for e in ["&amp;", "&lt;", "&gt;", "&quot;"]),
            f"{label} contains unescaped HTML entity: {text!r}"
        )

        # Check for method-call pattern e.g. Test.allTheThings()
        # Dot alone (Dr. Pepper) and parens alone (Kit (Bundle)) are fine
        check.is_false(
            bool(re.search(r'\w+\.\w+\(\)', text)),
            f"{label} contains method-like pattern (possible unresolved code): {text!r}"
        )
