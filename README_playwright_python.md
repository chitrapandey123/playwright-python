# playwright-python — Playwright Python Automation Framework

> Automation framework for [saucedemo.com](https://www.saucedemo.com) using Playwright Python + pytest + Page Object Model

[![CI](https://github.com/chitrapandey123/playwright-python/actions/workflows/playwright.yml/badge.svg)](https://github.com/chitrapandey123/playwright-python/actions)
[![Allure Report](https://img.shields.io/badge/Allure-Report-orange)](https://chitrapandey123.github.io/playwright-python/allure-history/)

---

## Allure Report

```
https://chitrapandey123.github.io/playwright-python/allure-history/
```

---

## Project Structure

```
playwright-python/
├── pages/
│   ├── base_page.py         # Base class with common methods
│   ├── login_page.py        # Login, logout assertions
│   ├── products_page.py     # Product listing, add/remove to cart
│   ├── cart_page.py         # Cart page, item verification
│   └── checkout_page.py     # Checkout flow
├── tests/
│   ├── test_login.py        # Login + logout test cases
│   ├── test_cart.py         # Cart test cases
│   └── test_products.py     # Product listing test cases
├── data/
│   └── testdata.json        # All test data (users, products, errors)
├── conftest.py              # pytest fixtures
├── pytest.ini               # pytest config with Allure
├── requirements.txt         # Dependencies
└── .github/
    └── workflows/
        └── playwright.yml   # CI/CD with Allure reporting
```

---

## Page Objects

| Page | File | Key Methods |
|------|------|-------------|
| Login | `login_page.py` | `login()`, `assert_login_success()`, `assert_error_message()`, `assert_logout_success()` |
| Products | `products_page.py` | `goto()`, `add_product_to_cart()`, `remove_product_from_cart()`, `assert_cart_count()`, `logout()` |
| Cart | `cart_page.py` | `goto()`, `assert_item_in_cart()`, `assert_cart_is_empty()`, `proceed_to_checkout()` |
| Checkout | `checkout_page.py` | `fill_shipping_info()`, `continue_to_overview()`, `finish_checkout()`, `assert_order_complete()` |

---

## Fixtures (conftest.py)

| Fixture | Returns | Purpose |
|---------|---------|---------|
| `test_data` | dict | Loads `data/testdata.json` once per session |
| `login_page` | LoginPage | Navigates to login page |
| `products_page` | ProductsPage | ProductsPage object (no navigation) |
| `cart_page` | CartPage | CartPage object |
| `checkout_page` | CheckoutPage | CheckoutPage object |
| `logged_in` | LoginPage | Logs in as standard user, returns LoginPage |

### Fixture usage patterns

```python
# Test login functionality
def test_login(self, login_page, test_data):
    login_page.login(test_data["users"]["standard"]["username"], ...)
    login_page.assert_login_success()

# Test when logged in state needed
def test_add_to_cart(self, logged_in, products_page, test_data):
    products_page.add_product_to_cart(test_data["products"]["backpack"])

# Test logout
def test_logout(self, logged_in, products_page):
    products_page.logout()
    logged_in.assert_logout_success()
```

---

## Test Data (testdata.json)

```json
{
  "users": {
    "standard": { "username": "standard_user", "password": "secret_sauce" },
    "locked": { "username": "locked_out_user", "password": "secret_sauce" },
    "invalid": { "username": "invalid_user", "password": "wrong_password" }
  },
  "products": {
    "backpack": "Sauce Labs Backpack",
    "bike_light": "Sauce Labs Bike Light"
  },
  "errors": {
    "locked_user": "Epic sadface: Sorry, this user has been locked out.",
    "invalid_credentials": "Epic sadface: Username and password do not match...",
    "empty_username": "Epic sadface: Username is required",
    "empty_password": "Epic sadface: Password is required"
  }
}
```

---

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run all tests (headless)
pytest -v

# Run with browser visible
pytest --headed -v

# Run specific file
pytest tests/test_login.py -v

# Run specific test
pytest tests/test_login.py::TestLogin::test_successful_login -v

# Run and view Allure report locally
pytest -v
allure serve allure-results
```

---

## CI/CD

Tests run automatically on every branch push via GitHub Actions:

1. pytest runs → generates `allure-results/`
2. Allure CLI generates HTML report
3. Report deployed to `gh-pages` branch
4. Available at: `https://chitrapandey123.github.io/playwright-python/allure-history/`

---

## Integration with TC Generator

This framework is the target for [TC Generator](https://github.com/chitrapandey123/tc-generator).

When TC Generator runs automation:
1. Reads all existing files from this repo
2. Generates new test methods with `allure.step()` blocks
3. Creates missing page objects if needed
4. Updates `testdata.json` with missing keys
5. Pushes all changes in ONE commit to branch `tc-{stories}-{timestamp}`
6. CI triggers automatically

---

## Author

Chitra Pandey — QA Engineer | [github.com/chitrapandey123](https://github.com/chitrapandey123)
