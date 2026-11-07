# Retail Online Store

A responsive Flask storefront demo for browsing and searching products, creating accounts, managing a cart, and placing demo orders. It does not collect payment details or process real payments. The original static demo files at the repository root are preserved and available at `/legacy`.

## Features

- Responsive storefront and product catalog
- Product search and category filtering
- Session cart with validated quantities and server-calculated prices
- Registration and login using Werkzeug password hashing
- SQLite persistence for demo accounts and orders
- Demo checkout only; no payment integration
- CSRF token checks on state-changing forms

## Requirements

Python 3.9 or later. Install the dependency from `requirements.txt`.

## Run locally

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. The app creates `store.db` on first run. For deployment, set a unique private `SECRET_KEY`; optionally set `STORE_DATABASE` to choose another SQLite file. Do not use debug mode in production.

## Routes

- `/` and `/catalog` — storefront, search, categories
- `/cart` — cart quantity updates and totals
- `/register`, `/login`, `/logout` — account flows
- `/checkout` — demo order creation
- `/health` — health check
- `/legacy` — original static demo

## Tests

```bash
python -m unittest discover -s tests -v
```

## Note

This is an educational demo, not production commerce software. Checkout records an order for demonstration; it never charges a customer.
