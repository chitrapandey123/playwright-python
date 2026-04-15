# Playwright Python Framework — Swag Labs

Automation framework for [saucedemo.com](https://www.saucedemo.com) using Playwright + Python + pytest.

## Structure

```
playwright-python/
├── conftest.py              ← pytest fixtures (login, pages, test data)
├── pytest.ini               ← pytest config
├── requirements.txt
├── .env                     ← BASE_URL, credentials
├── pages/                   ← Page Object Model
│   ├── base_page.py         ← Base class for all pages
│   ├── login_page.py        ← Login actions + assertions
│   ├── products_page.py     ← Products/inventory page
│   ├── cart_page.py         ← Cart page
│   └── checkout_page.py     ← Checkout (3 steps)
├── data/
│   └── testdata.json        ← Users, products, error messages
└── tests/
    └── test_login.py        ← Generated test files go here
```

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
playwright install
```

## Run tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_login.py

# Headless (no browser window)
pytest --headless

# With HTML report
pytest --html=report.html

# Specific browser
pytest --browser firefox
pytest --browser webkit
```

## Adding new test cases

TC Generator will automatically:
1. Read existing test files from GitHub
2. Add new tests without duplicating
3. Use existing Page Objects and fixtures
4. Preserve all existing imports and helpers

## Test users

| Username | Password | Type |
|----------|----------|------|
| standard_user | secret_sauce | Normal |
| locked_out_user | secret_sauce | Locked |
| problem_user | secret_sauce | UI issues |
| performance_glitch_user | secret_sauce | Slow |
