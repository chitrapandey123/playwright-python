import re
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class CartPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_title = page.locator(".title")
        self.cart_items = page.locator(".cart_item")
        self.checkout_button = page.locator('[data-test="checkout"]')
        self.continue_shopping_button = page.locator('[data-test="continue-shopping"]')
        self.cart_item_names = page.locator(".inventory_item_name")
        self.cart_item_prices = page.locator(".inventory_item_price")

    def goto(self):
        self.navigate_to("/cart.html")

    def get_cart_item_count(self) -> int:
        return self.cart_items.count()

    def remove_item(self, product_name: str):
        item = self.page.locator(".cart_item").filter(has_text=product_name)
        item.locator("button").click()

    def get_cart_item_names(self) -> list:
        return self.cart_item_names.all_inner_texts()

    def is_item_in_cart(self, product_name: str) -> bool:
        return self.page.locator(".inventory_item_name").filter(
            has_text=product_name
        ).is_visible()

    def proceed_to_checkout(self):
        self.checkout_button.click()

    def continue_shopping(self):
        self.continue_shopping_button.click()

    def assert_on_cart_page(self):
        expect(self.page).to_have_url(re.compile(r".*cart.*"))
        expect(self.page_title).to_have_text("Your Cart")

    def assert_cart_is_empty(self):
        expect(self.cart_items).to_have_count(0)

    def assert_item_in_cart(self, product_name: str):
        expect(
            self.page.locator(".inventory_item_name").filter(has_text=product_name)
        ).to_be_visible()

    def assert_cart_item_count(self, count: int):
        expect(self.cart_items).to_have_count(count)
