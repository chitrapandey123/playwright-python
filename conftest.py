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
    return lp


# Auto-attach screenshot on test failure
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            screenshot = page.screenshot()
            allure.attach(
                screenshot,
                name="Screenshot on failure",
                attachment_type=allure.attachment_type.PNG,
            )
