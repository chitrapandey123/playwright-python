import re
import allure
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class CheckoutPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        # Step 1 - Info
        self.first_name_input = page.locator('[data-test="firstName"]')
        self.last_name_input = page.locator('[data-test="lastName"]')
        self.postal_code_input = page.locator('[data-test="postalCode"]')
        self.continue_button = page.locator('[data-test="continue"]')
        self.cancel_button = page.locator('[data-test="cancel"]')
        self.error_message = page.locator('[data-test="error"]')

        # Step 2 - Overview
        self.summary_items = page.locator(".cart_item")
        self.subtotal_label = page.locator(".summary_subtotal_label")
        self.tax_label = page.locator(".summary_tax_label")
        self.total_label = page.locator(".summary_total_label")
        self.finish_button = page.locator('[data-test="finish"]')

        # Step 3 - Complete
        self.complete_header = page.locator(".complete-header")
        self.complete_text = page.locator(".complete-text")
        self.back_home_button = page.locator('[data-test="back-to-products"]')

    @allure.step("Fill shipping info: {first_name} {last_name}, {postal_code}")
    def fill_shipping_info(self, first_name: str, last_name: str, postal_code: str):
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.postal_code_input.fill(postal_code)

    @allure.step("Continue to order overview")
    def continue_to_overview(self):
        self.continue_button.click()

    @allure.step("Finish checkout")
    def finish_checkout(self):
        self.finish_button.click()

    @allure.step("Cancel checkout")
    def cancel_checkout(self):
        self.cancel_button.click()

    @allure.step("Back to products")
    def back_to_products(self):
        self.back_home_button.click()

    def get_total_price(self) -> str:
        return self.total_label.inner_text()

    @allure.step("Assert user is on checkout step 1")
    def assert_on_checkout_step1(self):
        expect(self.page).to_have_url(re.compile(r".*checkout-step-one.*"))

    @allure.step("Assert user is on checkout step 2")
    def assert_on_checkout_step2(self):
        expect(self.page).to_have_url(re.compile(r".*checkout-step-two.*"))

    @allure.step("Assert order is complete")
    def assert_order_complete(self):
        expect(self.page).to_have_url(re.compile(r".*checkout-complete.*"))
        expect(self.complete_header).to_have_text("Thank you for your order!")

    @allure.step("Assert error message: '{message}'")
    def assert_error_message(self, message: str):
        expect(self.error_message).to_be_visible()
        expect(self.error_message).to_contain_text(message)
