from __future__ import annotations

import json
import os
import secrets
import sqlite3
import uuid
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "local-demo-secret-change-before-deployment"),
    DATABASE=os.environ.get("STORE_DATABASE", str(BASE_DIR / "store.db")),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

PRODUCTS = [
    {"id": 1, "name": "Aurora Wireless Headphones", "category": "Electronics", "price": 1499, "description": "Noise-isolating wireless headphones with deep bass and up to 20 hours of battery life.", "emoji": "🎧"},
    {"id": 2, "name": "Summit Smart Watch", "category": "Accessories", "price": 2199, "description": "Track fitness, sleep, and notifications with a sleek stainless finish.", "emoji": "⌚"},
    {"id": 3, "name": "Harbor Canvas Backpack", "category": "Lifestyle", "price": 999, "description": "A durable everyday backpack with a padded laptop sleeve and weather-ready fabric.", "emoji": "🎒"},
    {"id": 4, "name": "Luma Desk Lamp", "category": "Home", "price": 1799, "description": "Adjustable LED lighting with warm and cool modes for productive workspaces.", "emoji": "💡"},
    {"id": 5, "name": "Terra Coffee Grinder", "category": "Kitchen", "price": 1299, "description": "Compact burr grinder for quick, cafe-style brews at home.", "emoji": "☕"},
    {"id": 6, "name": "Breeze Travel Bottle", "category": "Fitness", "price": 699, "description": "Insulated stainless steel bottle that keeps drinks cold throughout the day.", "emoji": "🧴"},
]
CATEGORIES = sorted({p["category"] for p in PRODUCTS})
PRODUCT_BY_ID = {p["id"]: p for p in PRODUCTS}
MAX_QUANTITY = 99


def get_db():
    db_path = Path(app.config["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, order_number TEXT UNIQUE NOT NULL, total INTEGER NOT NULL, items TEXT NOT NULL, address TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id))"
        )


def money(value):
    return f"₹{int(value):,}"


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.before_request
def protect_post_requests():
    if request.method == "POST" and not app.testing:
        supplied = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not supplied or not expected or not secrets.compare_digest(supplied, expected):
            abort(400, description="Invalid or missing form token. Reload the page and try again.")


@app.context_processor
def template_context():
    return {
        "current_user": get_current_user(),
        "cart_count": cart_count(),
        "csrf_token": csrf_token,
        "money": money,
    }


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as connection:
        row = connection.execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def get_cart():
    value = session.get("cart", {})
    return value if isinstance(value, dict) else {}


def cart_count():
    total = 0
    for item in get_cart().values():
        try:
            total += max(0, min(MAX_QUANTITY, int(item.get("quantity", 0))))
        except (AttributeError, TypeError, ValueError):
            continue
    return total


def parse_quantity(value):
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return None
    return quantity if 1 <= quantity <= MAX_QUANTITY else None


def build_cart_items():
    items = []
    subtotal = 0
    cart = get_cart()
    for key, entry in cart.items():
        try:
            product_id = int(key)
            quantity = int(entry.get("quantity", 0))
        except (AttributeError, TypeError, ValueError):
            continue
        product = PRODUCT_BY_ID.get(product_id)
        if not product or not 1 <= quantity <= MAX_QUANTITY:
            continue
        line_total = product["price"] * quantity
        subtotal += line_total
        items.append({**product, "quantity": quantity, "line_total": line_total})
    return items, subtotal


def filter_products(query="", category=""):
    products = PRODUCTS
    if category:
        products = [p for p in products if p["category"].casefold() == category.casefold()]
    if query:
        needle = query.casefold()
        products = [p for p in products if needle in " ".join((p["name"], p["category"], p["description"])).casefold()]
    return products


@app.route("/")
@app.route("/catalog")
def home():
    query = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    return render_template(
        "index.html", products=filter_products(query, category), query=query,
        categories=CATEGORIES, selected_category=category,
    )


@app.route("/legacy")
def legacy():
    return app.send_static_file("../index.html") if False else __import__("flask").send_from_directory(BASE_DIR, "index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirmation = request.form.get("confirm_password") or ""
        if not name or not email or not password:
            flash("Please fill in every field.", "error")
            return render_template("register.html")
        if len(name) > 100 or len(email) > 254 or "@" not in email:
            flash("Enter a valid name and email address.", "error")
            return render_template("register.html")
        if len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
            return render_template("register.html")
        if password != confirmation:
            flash("The passwords do not match.", "error")
            return render_template("register.html")
        try:
            with get_db() as connection:
                cursor = connection.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            flash("An account already exists for that email.", "error")
            return render_template("register.html")
        session.clear()
        session["user_id"] = user_id
        csrf_token()
        flash("Your account is ready. Welcome!", "success")
        return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        with get_db() as connection:
            user = connection.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            csrf_token()
            flash("You are logged in.", "success")
            return redirect(url_for("home"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You are logged out.", "success")
    return redirect(url_for("home"))


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = PRODUCT_BY_ID.get(product_id)
    quantity = parse_quantity(request.form.get("quantity", "1"))
    if not product or quantity is None:
        flash("That product or quantity is invalid.", "error")
        return redirect(url_for("home"))
    cart = get_cart()
    key = str(product_id)
    current = parse_quantity(cart.get(key, {}).get("quantity", 0)) if key in cart else 0
    new_quantity = current + quantity
    if new_quantity > MAX_QUANTITY:
        flash(f"You can add at most {MAX_QUANTITY} of each product.", "error")
    else:
        cart[key] = {"quantity": new_quantity}
        session["cart"] = cart
        flash(f"{product['name']} added to your cart.", "success")
    return redirect(url_for("cart"))


@app.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "POST":
        cart_data = get_cart()
        item_id = request.form.get("item_id", "")
        action = request.form.get("action")
        if item_id not in cart_data or item_id not in {str(p["id"]) for p in PRODUCTS}:
            flash("That cart item was not found.", "error")
            return redirect(url_for("cart"))
        if action == "remove":
            cart_data.pop(item_id, None)
            session["cart"] = cart_data
            flash("Item removed.", "success")
        elif action == "update":
            quantity = parse_quantity(request.form.get("quantity"))
            if quantity is None:
                flash(f"Quantity must be between 1 and {MAX_QUANTITY}.", "error")
            else:
                cart_data[item_id] = {"quantity": quantity}
                session["cart"] = cart_data
                flash("Cart updated.", "success")
        return redirect(url_for("cart"))
    items, subtotal = build_cart_items()
    return render_template("cart.html", cart_items=items, subtotal=subtotal)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if not get_current_user():
        flash("Please log in before checking out.", "error")
        return redirect(url_for("login"))
    items, subtotal = build_cart_items()
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))
    if request.method == "POST":
        address = (request.form.get("address") or "").strip()
        if not address or len(address) > 500:
            flash("Please provide a delivery address (up to 500 characters).", "error")
            return render_template("checkout.html", cart_items=items, subtotal=subtotal, success=False)
        order_number = "RS-" + uuid.uuid4().hex[:10].upper()
        with get_db() as connection:
            connection.execute(
                "INSERT INTO orders (user_id, order_number, total, items, address) VALUES (?, ?, ?, ?, ?)",
                (session["user_id"], order_number, subtotal, json.dumps(items), address),
            )
        session["cart"] = {}
        return render_template(
            "checkout.html", cart_items=items, subtotal=subtotal,
            success=True, order_number=order_number,
        )
    return render_template("checkout.html", cart_items=items, subtotal=subtotal, success=False)


@app.route("/health")
def health():
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="127.0.0.1", port=5000)
