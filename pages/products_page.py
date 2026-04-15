import re
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class ProductsPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_title = page.locator(".title")
        self.product_items = page.locator(".inventory_item")
        self.cart_icon = page.locator(".shopping_cart_link")
        self.cart_badge = page.locator(".shopping_cart_badge")
        self.sort_dropdown = page.locator('[data-test="product_sort_container"]')
        self.burger_menu = page.locator("#react-burger-menu-btn")
        self.logout_link = page.locator("#logout_sidebar_link")

    def goto(self):
        self.navigate_to("/inventory.html")

    def get_product_count(self) -> int:
        return self.product_items.count()

    def add_product_to_cart(self, product_name: str):
        product = self.page.locator(".inventory_item").filter(has_text=product_name)
        product.locator("button").click()

    def remove_product_from_cart(self, product_name: str):
        product = self.page.locator(".inventory_item").filter(has_text=product_name)
        product.locator("button").click()

    def get_cart_count(self) -> str:
        return self.cart_badge.inner_text()

    def is_cart_badge_visible(self) -> bool:
        return self.cart_badge.is_visible()

    def go_to_cart(self):
        self.cart_icon.click()

    def click_product(self, product_name: str):
        self.page.locator(".inventory_item_name").filter(has_text=product_name).click()

    def sort_products(self, option: str):
        # options: 'az', 'za', 'lohi', 'hilo'
        self.sort_dropdown.select_option(option)

    def logout(self):
        self.burger_menu.click()
        self.logout_link.click()

    def get_product_names(self) -> list:
        return self.page.locator(".inventory_item_name").all_inner_texts()

    def get_product_prices(self) -> list:
        return self.page.locator(".inventory_item_price").all_inner_texts()

    def assert_on_products_page(self):
        expect(self.page).to_have_url(re.compile(r".*inventory.*"))
        expect(self.page_title).to_have_text("Products")

    def assert_cart_count(self, count: str):
        expect(self.cart_badge).to_have_text(count)
