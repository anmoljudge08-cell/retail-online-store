"""SQLite persistence for Aurum & Ivy.

A single module owns the schema, the seed data and connection handling so the
Flask app never touches raw SQLite handles directly.
"""

from __future__ import annotations

import json
import os
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from werkzeug.security import generate_password_hash

import catalog

BASE_DIR = Path(__file__).resolve().parent
SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    slug         TEXT UNIQUE NOT NULL,
    name         TEXT NOT NULL,
    category     TEXT NOT NULL,
    price        INTEGER NOT NULL,
    compare_at   INTEGER NOT NULL DEFAULT 0,
    stock        INTEGER NOT NULL DEFAULT 0,
    featured     INTEGER NOT NULL DEFAULT 0,
    badge        TEXT NOT NULL DEFAULT '',
    image        TEXT NOT NULL,
    tagline      TEXT NOT NULL DEFAULT '',
    summary      TEXT NOT NULL DEFAULT '',
    description  TEXT NOT NULL DEFAULT '',
    details      TEXT NOT NULL DEFAULT '[]',
    materials    TEXT NOT NULL DEFAULT '',
    variants     TEXT NOT NULL DEFAULT '[]',
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'customer',
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number    TEXT UNIQUE NOT NULL,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email           TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    phone           TEXT NOT NULL DEFAULT '',
    address_line    TEXT NOT NULL,
    city            TEXT NOT NULL,
    state           TEXT NOT NULL DEFAULT '',
    postal_code     TEXT NOT NULL,
    country         TEXT NOT NULL DEFAULT 'India',
    subtotal        INTEGER NOT NULL DEFAULT 0,
    discount        INTEGER NOT NULL DEFAULT 0,
    shipping        INTEGER NOT NULL DEFAULT 0,
    tax             INTEGER NOT NULL DEFAULT 0,
    total           INTEGER NOT NULL DEFAULT 0,
    promo_code      TEXT NOT NULL DEFAULT '',
    delivery_method TEXT NOT NULL DEFAULT 'standard',
    payment_method  TEXT NOT NULL DEFAULT 'card',
    note            TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'Processing',
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    slug       TEXT NOT NULL DEFAULT '',
    name       TEXT NOT NULL,
    variant    TEXT NOT NULL DEFAULT '',
    unit_price INTEGER NOT NULL,
    quantity   INTEGER NOT NULL,
    image      TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS reviews (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    author     TEXT NOT NULL,
    rating     INTEGER NOT NULL,
    title      TEXT NOT NULL DEFAULT '',
    body       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishlist (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS newsletter (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
"""


# --------------------------------------------------------------------------- paths
def database_path() -> str:
    """Resolve the SQLite file.

    Serverless platforms give a read-only filesystem apart from /tmp, so the
    deployed demo keeps its database there (it resets on cold start, which is
    fine for a demo dataset that reseeds itself).
    """
    configured = os.environ.get("STORE_DATABASE")
    if configured:
        return configured
    if SERVERLESS:
        return "/tmp/aurum-ivy.db"
    return str(BASE_DIR / "instance" / "store.db")


def connect(path: str | None = None) -> sqlite3.Connection:
    target = path or database_path()
    if target != ":memory:":
        Path(target).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


# --------------------------------------------------------------------------- seeding
def _seed_products(connection: sqlite3.Connection) -> None:
    for item in catalog.PRODUCTS:
        connection.execute(
            """
            INSERT INTO products (slug, name, category, price, compare_at, stock, featured,
                                  badge, image, tagline, summary, description, details,
                                  materials, variants)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO NOTHING
            """,
            (
                item["slug"], item["name"], item["category"], item["price"],
                item.get("compare_at", 0), item["stock"], item.get("featured", 0),
                item.get("badge", ""), item["image"], item.get("tagline", ""),
                item["summary"], item["description"], json.dumps(item["details"]),
                item["materials"], json.dumps(item["variants"]),
            ),
        )


def _seed_reviews(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]:
        return
    ids = {row["slug"]: row["id"] for row in connection.execute("SELECT id, slug FROM products")}
    base = datetime.now(timezone.utc)
    for index, (slug, author, rating, title, body) in enumerate(catalog.REVIEWS):
        product_id = ids.get(slug)
        if not product_id:
            continue
        created = (base - timedelta(days=12 + index * 9)).strftime("%Y-%m-%d %H:%M:%S")
        connection.execute(
            "INSERT INTO reviews (product_id, author, rating, title, body, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (product_id, author, rating, title, body, created),
        )


def _seed_users(connection: sqlite3.Connection) -> None:
    accounts = [
        ("Aurum Concierge", "admin@aurumivy.com", "admin1234", "admin"),
        ("Demo Customer", "demo@aurumivy.com", "demo1234", "customer"),
    ]
    for name, email, password, role in accounts:
        connection.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(email) DO NOTHING
            """,
            (name, email, generate_password_hash(password), role),
        )


def _seed_orders(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]:
        return

    user = connection.execute("SELECT id, name, email FROM users WHERE email = ?", ("demo@aurumivy.com",)).fetchone()
    if user is None:
        return

    products = {row["slug"]: row for row in connection.execute("SELECT * FROM products")}
    now = datetime.now(timezone.utc)

    demo_orders = [
        {
            "number": "AI-100241",
            "status": "Delivered",
            "days_ago": 47,
            "lines": [("meridian-anc-headphones", "Ivory / Brass", 1), ("fold-leather-cardholder", "Chestnut", 2)],
            "payment": "card",
            "delivery": "express",
        },
        {
            "number": "AI-100388",
            "status": "Shipped",
            "days_ago": 6,
            "lines": [("nocturne-cashmere-throw", "Emerald", 1), ("voyage-insulated-flask", "Emerald", 2)],
            "payment": "upi",
            "delivery": "standard",
        },
    ]

    for spec in demo_orders:
        subtotal = 0
        priced = []
        for slug, variant, quantity in spec["lines"]:
            product = products[slug]
            subtotal += product["price"] * quantity
            priced.append((product, variant, quantity))

        shipping = catalog.SHIPPING["express"] if spec["delivery"] == "express" else (
            0 if subtotal >= catalog.SHIPPING["free_threshold"] else catalog.SHIPPING["standard"]
        )
        tax = int(round(subtotal * catalog.TAX_RATE))
        total = subtotal + shipping + tax
        created = (now - timedelta(days=spec["days_ago"])).strftime("%Y-%m-%d %H:%M:%S")

        cursor = connection.execute(
            """
            INSERT INTO orders (order_number, user_id, email, full_name, phone, address_line, city,
                                state, postal_code, country, subtotal, discount, shipping, tax,
                                total, promo_code, delivery_method, payment_method, note, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spec["number"], user["id"], user["email"], user["name"], "+91 98200 11223",
                "14 Bandra West, Pali Hill", "Mumbai", "Maharashtra", "400050", "India",
                subtotal, 0, shipping, tax, total, "", spec["delivery"], spec["payment"], "",
                spec["status"], created,
            ),
        )
        order_id = cursor.lastrowid
        for product, variant, quantity in priced:
            connection.execute(
                """
                INSERT INTO order_items (order_id, product_id, slug, name, variant, unit_price, quantity, image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, product["id"], product["slug"], product["name"], variant,
                 product["price"], quantity, product["image"]),
            )


def init_db(path: str | None = None, seed: bool = True) -> str:
    """Create the schema and demo data if needed. Returns the database path."""
    target = path or database_path()
    connection = connect(target)
    try:
        connection.executescript(SCHEMA)
        if seed:
            _seed_products(connection)
            _seed_reviews(connection)
            _seed_users(connection)
            _seed_orders(connection)
        connection.commit()
    finally:
        connection.close()
    return target


def reset_db(path: str | None = None) -> None:
    """Drop every table and reseed. Used by the test-suite and the CLI."""
    target = path or database_path()
    connection = connect(target)
    try:
        connection.executescript(SCHEMA)
        for table in ("order_items", "orders", "reviews", "wishlist", "products", "users", "newsletter"):
            connection.execute(f"DELETE FROM {table}")
        try:
            connection.execute("DELETE FROM sqlite_sequence")
        except sqlite3.OperationalError:
            pass
        connection.commit()
    finally:
        connection.close()
    init_db(target)


def new_order_number(connection: sqlite3.Connection) -> str:
    """Human-friendly, collision-checked order reference."""
    while True:
        candidate = f"AI-{random.randint(100000, 999999)}"
        if not connection.execute("SELECT 1 FROM orders WHERE order_number = ?", (candidate,)).fetchone():
            return candidate


if __name__ == "__main__":  # pragma: no cover - CLI helper
    location = init_db()
    print(f"Database ready at {location}")
