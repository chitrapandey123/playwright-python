import re
import allure
from playwright.sync_api import Page, expect
from pages.base_page import BasePage
import time


class ProductsPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_title = page.locator(".title")
        self.inventory_items = page.locator(".inventory_item")
        self.cart_badge = page.locator(".shopping_cart_badge")
        self.cart_link = page.locator(".shopping_cart_link")
        self.sort_dropdown = page.locator('[data-test="product_sort_container"]')
        self.menu_button = page.locator("#react-burger-menu-btn_wrong")
        self.logout_link = page.locator("#logout_sidebar_link")

    @allure.step("Navigate to products page")
    def goto(self):
        self.navigate_to("/inventory.html")

    def get_product_card(self, product_name: str):
        return self.page.locator(".inventory_item").filter(has_text=product_name)

    @allure.step("Add '{product_name}' to cart")
    def add_product_to_cart(self, product_name: str):
        product_card = self.get_product_card(product_name)
        product_card.locator("button").click()

    @allure.step("Remove '{product_name}' from cart")
    def remove_product_from_cart(self, product_name: str):
        product_card = self.get_product_card(product_name)
        product_card.locator("button").click()

    def get_product_button_text(self, product_name: str) -> str:
        product_card = self.get_product_card(product_name)
        return product_card.locator("button").inner_text()

    def get_cart_badge_count(self) -> int:
        if self.cart_badge.is_visible():
            return int(self.cart_badge.inner_text())
        return 0

    @allure.step("Go to cart")
    def go_to_cart(self):
        self.cart_link.click()

    def get_all_product_names(self) -> list:
        return self.page.locator(".inventory_item_name").all_inner_texts()

    def get_product_price(self, product_name: str) -> str:
        product_card = self.get_product_card(product_name)
        return product_card.locator(".inventory_item_price").inner_text()

    @allure.step("Assert user is on products page")
    def assert_on_products_page(self):
        expect(self.page).to_have_url(re.compile(r".*inventory.*"))
        expect(self.page_title).to_have_text("Products")

    @allure.step("Assert '{product_name}' button shows '{expected_text}'")
    def assert_product_button_text(self, product_name: str, expected_text: str):
        product_card = self.get_product_card(product_name)
        expect(product_card.locator("button")).to_have_text(expected_text)

    @allure.step("Assert cart badge count is {count}")
    def assert_cart_badge_count(self, count: int):
        if count == 0:
            expect(self.cart_badge).not_to_be_visible()
        else:
            expect(self.cart_badge).to_have_text(str(count))

    @allure.step("Assert cart badge is not visible")
    def assert_cart_badge_not_visible(self):
        expect(self.cart_badge).not_to_be_visible()

    @allure.step("Click cart icon")
    def click_cart_icon(self):
        self.cart_link.click()

    @allure.step("Assert products page is displayed")
    def assert_products_page_displayed(self):
        expect(self.page).to_have_url(re.compile(r".*inventory.*"))
        expect(self.page_title).to_have_text("Products")

    @allure.step("Assert all products have required elements")
    def assert_all_products_have_required_elements(self):
        items = self.inventory_items.all()
        assert len(items) > 0, "No products found on the page"
        for item in items:
            expect(item.locator("img.inventory_item_img")).to_be_visible()
            expect(item.locator(".inventory_item_name")).to_be_visible()
            expect(item.locator(".inventory_item_price")).to_be_visible()
            expect(item.locator("button")).to_be_visible()

    @allure.step("Assert all product images loaded correctly")
    def assert_all_product_images_loaded(self):
        items = self.inventory_items.all()
        assert len(items) > 0, "No products found on the page"
        for item in items:
            img = item.locator("img.inventory_item_img")
            expect(img).to_be_visible()
            src = img.get_attribute("src")
            assert src is not None and src != "", "Product image has no src attribute"
            assert "sl-404" not in src.lower(), "Product image appears to be broken (404 placeholder)"

    @allure.step("Logout")
    def logout(self):
        self.menu_button.wait_for(state="visible")
        self.menu_button.click()
        self.logout_link.wait_for(state="visible")
        self.logout_link.click()
        self.page.wait_for_load_state("networkidle")
