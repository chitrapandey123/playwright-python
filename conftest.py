import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import pytest
import allure
from playwright.sync_api import Page
from pages.login_page import LoginPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage


@pytest.fixture(scope="session")
def test_data():
    with open(os.path.join(os.path.dirname(__file__), "data/testdata.json")) as f:
        return json.load(f)


@pytest.fixture
def login_page(page: Page):
    lp = LoginPage(page)
    lp.goto()
    return lp

@pytest.fixture
def login_page_obj(page: Page):
    """LoginPage object without navigation - use when already logged in"""
    return LoginPage(page)


@pytest.fixture
def products_page(page: Page):
    # Import here to handle case where products_page.py may not exist yet
    try:
        from pages.products_page import ProductsPage
        return ProductsPage(page)
    except ImportError:
        return None


@pytest.fixture
def cart_page(page: Page):
    return CartPage(page)


@pytest.fixture
def checkout_page(page: Page):
    return CheckoutPage(page)


@pytest.fixture
def logged_in(page: Page, test_data):
    lp = LoginPage(page)
    lp.goto()
    lp.login(
        test_data["users"]["standard"]["username"],
        test_data["users"]["standard"]["password"],
    )
    '''from pages.products_page import ProductsPage
    return ProductsPage(page)'''
    return lp


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            allure.attach(
                page.screenshot(),
                name="Screenshot on failure",
                attachment_type=allure.attachment_type.PNG,
            )
            allure.attach(
                page.url,
                name="URL on failure",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                page.content(),
                name="Page HTML on failure",
                attachment_type=allure.attachment_type.HTML,
            )
