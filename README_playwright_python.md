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
├── config/
│   └── prod.json            # Environment config (base_url, browser)
├── utils/
│   └── config.py            # Reads environment config file
├── auto_fix_agent.py        # AI-powered auto-fix agent (Claude)
├── conftest.py              # pytest fixtures + failure hooks
├── pytest.ini               # pytest config (parallel workers, Allure)
├── requirements.txt         # Dependencies
└── .github/
    └── workflows/
        └── playwright.yml   # CI/CD with Allure reporting + auto-fix agent
```

---

## Auto-Fix Agent

An AI-powered agent built with [Claude (Anthropic)](https://www.anthropic.com) that automatically detects, analyses, and fixes failing tests in CI without human intervention.

### How it works

```
Tests fail in CI
      ↓
Agent parses failures + reads source files
      ↓
Sends to Claude API for root cause analysis
      ↓
Claude returns fix plan (JSON)
      ↓
Agent applies fixes → re-runs tests to verify
      ↓
Creates branch + PR with before/after diff
```

### Features

- Triggers automatically in CI when tests fail
- Fixes wrong CSS selectors, locator IDs, and test data keys
- Re-runs tests after applying fixes to verify they pass
- Creates a GitHub PR with a detailed diff for human review
- Never modifies quality checks or soft assertions — leaves those for human review
- Skips fix if no code changes are needed (e.g. site is down, or quality check caught a real bug)
- Safe — always creates a new branch, never commits directly to main

### Example PR created by agent

```
fix: auto-fix failing Playwright tests [20260519-073712]

File : pages/cart_page.py
What : Fixed wrong CSS selector for cart items
Before: ".cart_item_WRONG"
After : ".cart_item"
```

---

## Parallel Execution

Tests run in parallel using `pytest-xdist` with 4 workers by default, reducing execution time by ~3x.

```
Without parallel (1 worker):   sequential → ~7s
With parallel (4 workers):     simultaneous → ~3s
```

Each worker gets its own browser instance — no shared state between workers.

```bash
# Default (4 workers, configured in pytest.ini)
pytest

# Override workers at runtime
pytest -n 2
pytest -n 8
```

In CI, all 4 workers run simultaneously and report results prefixed with `[gw0]`, `[gw1]`, `[gw2]`, `[gw3]`. The Allure **Timeline** tab shows the parallel execution visually after the run.

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

---

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run all tests (4 parallel workers by default)
pytest

# Run with browser visible
pytest --headed

# Run specific file
pytest tests/test_login.py -v

# Run and view Allure report locally
pytest
allure serve allure-results
```

---

## CI/CD

Tests run automatically on every branch push via GitHub Actions:

1. pytest runs with 4 parallel workers → generates `allure-results/`
2. Allure CLI generates HTML report
3. Report deployed to GitHub Pages per branch and run number
4. Clickable report link posted in the job Summary tab
5. Latest report always available at: `https://chitrapandey123.github.io/playwright-python/allure-history/`
6. If tests fail → Auto-Fix Agent triggers, analyses failures, and opens a PR with fixes

### Manual run with environment selection

Trigger from **Actions → Run workflow** and select the environment:

- `prod` — runs against production (default)

---

## Environment Config

Environment-specific settings live in `config/<env>.json`:

```json
{
  "base_url": "https://www.saucedemo.com",
  "browser": "chromium"
}
```

`utils/config.py` loads the correct file based on the `ENV` variable (defaults to `prod`).

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
