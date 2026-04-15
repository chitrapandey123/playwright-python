import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import os
import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage


# Load test data
@pytest.fixture(scope="session")
def test_data():
    with open(os.path.join(os.path.dirname(__file__), "data/testdata.json")) as f:
        return json.load(f)


# Page fixtures
@pytest.fixture
def login_page(page: Page):
    lp = LoginPage(page)
    lp.goto()
    return lp


@pytest.fixture
def products_page(page: Page):
    return ProductsPage(page)


@pytest.fixture
def cart_page(page: Page):
    return CartPage(page)


@pytest.fixture
def checkout_page(page: Page):
    return CheckoutPage(page)


# Pre-logged in fixture
@pytest.fixture
def logged_in(page: Page, test_data):
    lp = LoginPage(page)
    lp.goto()
    lp.login(
        test_data["users"]["standard"]["username"],
        test_data["users"]["standard"]["password"],
    )
    return ProductsPage(page)
