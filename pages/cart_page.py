import re
import allure
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class CartPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_title = page.locator(".title")
        self.cart_items = page.locator(".cart_item_WRONG")
        self.checkout_button = page.locator('[data-test="checkout"]')
        self.continue_shopping_button = page.locator('[data-test="continue-shopping"]')
        self.cart_item_names = page.locator(".inventory_item_name")
        self.cart_item_prices = page.locator(".inventory_item_price")
        self.cart_link = page.locator(".shopping_cart_link")

    @allure.step("Navigate to cart page")
    def goto(self):
        self.navigate_to("/cart.html")

    def get_cart_item_count(self) -> int:
        return self.cart_items.count()

    @allure.step("Remove '{product_name}' from cart")
    def remove_item(self, product_name: str):
        item = self.page.locator(".cart_item").filter(has_text=product_name)
        item.locator("button").click()

    def get_cart_item_names(self) -> list:
        return self.cart_item_names.all_inner_texts()

    def is_item_in_cart(self, product_name: str) -> bool:
        return self.page.locator(".inventory_item_name").filter(
            has_text=product_name
        ).is_visible()

    @allure.step("Proceed to checkout")
    def proceed_to_checkout(self):
        self.checkout_button.click()

    @allure.step("Continue shopping")
    def continue_shopping(self):
        self.continue_shopping_button.click()

    @allure.step("Assert user is on cart page")
    def assert_on_cart_page(self):
        expect(self.page).to_have_url(re.compile(r".*cart.*"))
        expect(self.page_title).to_have_text("Your Cart")

    @allure.step("Assert cart is empty")
    def assert_cart_is_empty(self):
        expect(self.cart_items).to_have_count(0)

    @allure.step("Assert '{product_name}' is in cart")
    def assert_item_in_cart(self, product_name: str):
        expect(
            self.page.locator(".inventory_item_name").filter(has_text=product_name)
        ).to_be_visible()

    @allure.step("Assert cart item count is {count}")
    def assert_cart_item_count(self, count: int):
        expect(self.cart_items).to_have_count(count)

    @allure.step("Assert cart page is loaded")
    def assert_cart_page_loaded(self):
        expect(self.page).to_have_url(re.compile(r".*cart.*"))
        expect(self.page_title).to_have_text("Your Cart")

    @allure.step("Assert '{product_name}' is in cart")
    def assert_product_in_cart(self, product_name: str):
        expect(
            self.page.locator(".inventory_item_name").filter(has_text=product_name)
        ).to_be_visible()

    @allure.step("Assert '{product_name}' price is '{expected_price}'")
    def assert_product_price(self, product_name: str, expected_price: str):
        item = self.page.locator(".cart_item").filter(has_text=product_name)
        expect(item.locator(".inventory_item_price")).to_have_text(expected_price)

    @allure.step("Assert '{product_name}' quantity is {expected_quantity}")
    def assert_product_quantity(self, product_name: str, expected_quantity: int):
        item = self.page.locator(".cart_item").filter(has_text=product_name)
        expect(item.locator(".cart_quantity")).to_have_text(str(expected_quantity))

    @allure.step("Click cart icon")
    def click_cart_icon(self):
        self.cart_link.click()
