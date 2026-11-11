# Aurum & Ivy — a full retail storefront in Flask

A complete, production-shaped online store for a small luxury house: catalogue, search and
filters, product pages with reviews, a session cart with promo codes, a validated checkout that
writes real orders and decrements stock, customer accounts, wishlists, order tracking, and an
admin dashboard.

**Palette** — deep emerald `#0B2B26`, champagne brass `#C6A266`, warm ivory `#F7F2E9`.
**Type** — Cormorant Garamond (display) and Jost (interface).

![Three-colour scheme](./static/img/meridian-headphones.jpg)

---

## What is in the box

| Area | What it does |
| --- | --- |
| Storefront | Editorial home page: hero, six collections, featured edit, atelier story, journal cards, testimonials, concierge band |
| Catalogue | Full-text search, category filter, price range, in-stock filter, six sort orders, pagination |
| Product pages | Variants, stock urgency, accordions for details/materials/delivery, rating distribution, customer reviews, related pieces |
| Cart | Slide-over drawer plus a full bag page, quantity steppers, stock-aware limits, progress meter to free delivery, promo codes |
| Checkout | Validated contact/address/delivery/payment details, four payment methods, live delivery totals, transactional stock decrement, order confirmation page with a progress timeline |
| Accounts | Register, sign in/out, order history, buy-again, wishlist, lifetime spend |
| Tracking | Guest lookup by order number + email, with the same delivery timeline |
| Admin | Revenue/order/customer/low-stock stats, order status updates, inline stock editing, best sellers |
| Security | CSRF tokens on every mutating form, hashed passwords, session cookie hardening, security headers + CSP, honeypot field, safe redirect handling |
| Quality | 42 end-to-end tests, no JavaScript required for any core flow |

---

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # http://localhost:5000
```

The SQLite database and demo data are created automatically on first run at
`instance/store.db`. Delete that file (or run `python -m db`) to reseed everything.

### Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Customer | `demo@aurumivy.com` | `demo1234` |
| Admin | `admin@aurumivy.com` | `admin1234` |

The customer account comes with two seeded orders so the account, tracking and admin screens are
not empty. **Change or remove these accounts before any real deployment.**

### Promo codes

| Code | Effect |
| --- | --- |
| `WELCOME10` | 10% off, capped at ₹2,000 |
| `AURUM15` | 15% off orders over ₹15,000, capped at ₹6,000 |
| `FREESHIP` | Complimentary delivery |

---

## Tests

```bash
python -m unittest discover -s tests -v
```

42 tests covering pages, filters, cart maths, promo rules, stock limits, checkout validation and
stock decrement, order privacy, tracking, registration/login, wishlist, reviews, reorder, admin
authorisation, CSRF rejection, security headers and seed idempotency.

---

## Project layout

```
app.py              Flask app: routes, cart maths, checkout, auth, admin, error handlers
catalog.py          Store settings, categories, the 10 products, reviews, promo rules
db.py               Schema, connection handling, seed data, order numbers
api/index.py        Vercel WSGI entrypoint
vercel.json         Vercel build + routes
templates/          base, home, shop, product, cart, checkout, order, auth, account, track, admin, error
static/css/store.css   Design system: palette, type, all components
static/js/store.js     Cart drawer, AJAX add/update, steppers, filters, checkout totals
static/img/          Optimised product photography (4:5, ~80 KB each)
tests/test_app.py   42 end-to-end tests
```

### Routes

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Home |
| GET | `/shop` | Catalogue (`q`, `category`, `sort`, `min_price`, `max_price`, `in_stock`, `page`) |
| GET | `/product/<slug>` | Product detail |
| POST | `/product/<slug>/review` | Publish a review (signed in) |
| GET | `/cart` · `/api/cart` | Bag page · JSON bag payload |
| POST | `/cart/add` `/cart/update` `/cart/remove` | Bag mutations (JSON when `X-Requested-With`) |
| POST | `/cart/promo` · `/cart/promo/remove` | Promo codes |
| GET/POST | `/checkout` | Checkout form and order creation |
| GET | `/order/<number>` | Confirmation / receipt |
| GET/POST | `/track` | Guest order lookup |
| GET/POST | `/login` `/register`, POST `/logout` | Accounts |
| GET | `/account` | Orders, wishlist, spend |
| POST | `/orders/<id>/reorder` | Buy again |
| POST | `/wishlist/toggle` | Save/unsave |
| POST | `/newsletter` | Subscribe |
| GET | `/admin`, POST `/admin/orders/<id>/status`, `/admin/products/<id>/stock` | Admin |
| GET | `/health` | Liveness + database path |

---

## Deploy to Vercel

The repository is already wired for Vercel (`vercel.json` + `api/index.py`):

```bash
npm i -g vercel        # once
vercel                 # preview deploy
vercel --prod          # production
```

`vercel.json` rewrites every request — assets included — to the Python function, and bundles
`templates/**` and `static/**` into it, so Flask serves the stylesheet and images itself. Nothing
depends on Vercel's own static-file handling. Asset URLs carry a `?v=` version so a previously
cached miss cannot mask a new deploy, and `GET /health` reports whether the CSS, JS and product
images are present in the running bundle.

Check a deployment with these two URLs:

* `/static/css/store.css?v=3` → should return CSS, not 404
* `/health` → `{"status":"ok","assets":{"css/store.css":true,…}}`

Set these environment variables in the Vercel project:

| Variable | Why |
| --- | --- |
| `SECRET_KEY` | Signing key for sessions and CSRF tokens. **Required in production.** |
| `STORE_DATABASE` | Optional. Defaults to `/tmp/aurum-ivy.db` on Vercel. |

> **Serverless note:** Vercel's filesystem is read-only apart from `/tmp`, and `/tmp` is not shared
> between instances. The demo therefore reseeds itself on cold start and orders are not permanent.
> For a real store, point `STORE_DATABASE` at a managed database (Postgres/Turso) or run the Flask
> app on a host with a persistent disk (Render, Railway, Fly.io, a VPS).

Any other WSGI host works without changes: `gunicorn app:app`.

---

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `SECRET_KEY` | dev placeholder | Set a long random value in production |
| `STORE_DATABASE` | `instance/store.db` (`/tmp/…` on Vercel) | SQLite file path |
| `PORT` | `5000` | Only used by `python app.py` |

Business rules live in `catalog.py`: free-delivery threshold (₹10,000), standard/express delivery
charges, 18% GST, and the promo table. Product copy, variants and seed reviews live there too.

---

## Notes on the demo

* Payments are simulated: card and UPI fields are collected for realism but nothing is charged and
  no card data is stored. Only the chosen method is saved on the order.
* Stock is decremented inside a transaction with a `WHERE stock >= ?` guard, so two shoppers cannot
  oversell the last unit.
* Order pages are visible only to the buyer, an admin, or the session that just placed the order;
  everyone else is sent to `/track`.
* Product photography in `static/img` is AI-generated for this demo.

---

© 2026 Aurum & Ivy (demo). Built with Flask and SQLite, no other runtime dependencies.
