import os
import re
import allure
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class LoginPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.locator("#user-name")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("#login-button")
        self.error_message = page.locator('[data-test="error"]')

    @allure.step("Navigate to login page")
    def goto(self):
        self.navigate_to("/")

    @allure.step("Login with username '{username}'")
    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    @allure.step("Login with valid user")
    def login_with_valid_user(self):
        self.login(
            os.getenv("VALID_USERNAME", "standard_user"),
            os.getenv("VALID_PASSWORD", "secret_sauce"),
        )

    def get_error_message(self) -> str:
        return self.error_message.inner_text()

    def is_error_visible(self) -> bool:
        return self.error_message.is_visible()

    @allure.step("Assert login was successful")
    def assert_login_success(self):
        expect(self.page).to_have_url(re.compile(r".*inventory.*"))

    @allure.step("Assert error message: '{message}'")
    def assert_error_message(self, message: str):
        expect(self.error_message).to_be_visible()
        expect(self.error_message).to_contain_text(message)

    @allure.step("Enter username: '{username}'")
    def enter_username(self, username: str):
        self.username_input.fill(username)

    @allure.step("Enter password")
    def enter_password(self, password: str):
        self.password_input.fill(password)

    @allure.step("Click login button")
    def click_login_button(self):
        self.login_button.click()

    @allure.step("Assert user is on login page")
    def assert_on_login_page(self):
        expect(self.login_button).to_be_visible()
        expect(self.username_input).to_be_visible()

    @allure.step("Assert logout was successful")
    def assert_logout_success(self):
        expect(self.page).to_have_url(re.compile(r".*saucedemo\.com/?$"))
        expect(self.login_button).to_be_visible()
        expect(self.username_input).to_be_visible()
