import os
import re
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class LoginPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.locator("#user-name")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("#login-button")
        self.error_message = page.locator('[data-test="error"]')

    def goto(self):
        self.navigate_to("/")

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def login_with_valid_user(self):
        self.login(
            os.getenv("VALID_USERNAME", "standard_user"),
            os.getenv("VALID_PASSWORD", "secret_sauce"),
        )

    def get_error_message(self) -> str:
        return self.error_message.inner_text()

    def is_error_visible(self) -> bool:
        return self.error_message.is_visible()

    def assert_login_success(self):
        expect(self.page).to_have_url(re.compile(r".*inventory.*"))

    def assert_error_message(self, message: str):
        expect(self.error_message).to_be_visible()
        expect(self.error_message).to_contain_text(message)
