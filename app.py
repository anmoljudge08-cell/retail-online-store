"""Aurum & Ivy — a complete Flask storefront.

Run locally:      python app.py
Reset demo data:  python -m db
Tests:            python -m unittest discover -s tests -v
"""

from __future__ import annotations

import functools
import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import catalog
import db

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "aurum-ivy-dev-secret-please-set-SECRET_KEY"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    TEMPLATES_AUTO_RELOAD=True,
)

# Bump to invalidate cached CSS/JS URLs (query-string versioning).
ASSET_VERSION = os.environ.get("ASSET_VERSION", "3")

# Production tightens framing; the sandbox/preview needs to be embeddable in an iframe.
PRODUCTION = bool(os.environ.get("VERCEL") or os.environ.get("STORE_ENV") == "production")

ORDER_STATUSES = ["Processing", "Packed", "Shipped", "Delivered", "Cancelled"]
PAYMENT_METHODS = {"card": "Credit / debit card", "upi": "UPI", "cod": "Cash on delivery"}
DELIVERY_METHODS = {"standard": "Standard — 3 to 5 days", "express": "Express — 1 to 2 days"}


# --------------------------------------------------------------------------- helpers
def format_money(value) -> str:
    """Indian digit grouping with a rupee sign: 124900 -> ₹1,24,900."""
    try:
        amount = int(round(float(value or 0)))
    except (TypeError, ValueError):
        amount = 0
    digits = str(abs(amount))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        head = re.sub(r"(?<=\d)(?=(\d{2})+$)", ",", head)
        digits = f"{head},{tail}"
    return f"{'-' if amount < 0 else ''}₹{digits}"


def format_date(value, fmt: str = "%d %b %Y") -> str:
    if not value:
        return ""
    if isinstance(value, str):
        for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                value = datetime.strptime(value, pattern)
                break
            except ValueError:
                continue
    if isinstance(value, datetime):
        return value.strftime(fmt)
    return str(value)


app.jinja_env.filters["money"] = format_money
app.jinja_env.filters["date_human"] = format_date
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = db.connect()
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def product_rows(where: str = "", params: tuple = (), order: str = "p.featured DESC, p.id ASC", limit: int | None = None, offset: int = 0):
    sql = f"""
        SELECT p.*,
               (SELECT COALESCE(AVG(r.rating), 0) FROM reviews r WHERE r.product_id = p.id) AS rating_avg,
               (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id) AS review_count
        FROM products p
        {where}
        ORDER BY {order}
    """
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params = (*params, limit, offset)
    products = rows_to_dicts(get_db().execute(sql, params).fetchall())
    for product in products:
        product["variants_list"] = json.loads(product["variants"] or "[]")
        product["details_list"] = json.loads(product["details"] or "[]")
        product["category_name"] = catalog.CATEGORY_NAMES.get(product["category"], product["category"].title())
    return products


def get_product(slug: str):
    products = product_rows("WHERE p.slug = ?", (slug,), limit=1)
    return products[0] if products else None


def cart_map() -> dict:
    cart = session.get("cart")
    return dict(cart) if isinstance(cart, dict) else {}


def save_cart(cart: dict) -> None:
    session["cart"] = {key: int(qty) for key, qty in cart.items() if int(qty) > 0}
    session.modified = True


def parse_key(key: str):
    if "|" not in key:
        return None, None
    raw_id, variant = key.split("|", 1)
    try:
        return int(raw_id), variant
    except ValueError:
        return None, None


def cart_lines() -> list[dict]:
    cart = cart_map()
    if not cart:
        return []
    ids = [pid for pid, _ in (parse_key(key) for key in cart) if pid]
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    products = {row["id"]: row for row in get_db().execute(f"SELECT * FROM products WHERE id IN ({placeholders})", ids)}

    lines = []
    for key, quantity in cart.items():
        product_id, variant = parse_key(key)
        product = products.get(product_id)
        if product is None:
            continue
        available = max(int(product["stock"]), 0)
        quantity = max(0, min(int(quantity), available))
        if quantity == 0:
            continue
        lines.append(
            {
                "key": key,
                "product_id": product["id"],
                "slug": product["slug"],
                "name": product["name"],
                "variant": variant or "",
                "image": product["image"],
                "unit_price": product["price"],
                "quantity": quantity,
                "line_total": product["price"] * quantity,
                "stock": available,
            }
        )
    return lines


def cart_totals(lines: list[dict], promo_code: str | None = None, delivery: str = "standard") -> dict:
    subtotal = sum(line["line_total"] for line in lines)
    promo = catalog.PROMOS.get((promo_code or "").strip().upper())
    discount = 0
    promo_applies = False
    free_shipping = False

    if promo and subtotal > 0 and subtotal >= promo["min_subtotal"]:
        promo_applies = True
        discount = min(int(round(subtotal * promo["percent"] / 100)), promo["max_discount"])
        free_shipping = bool(promo.get("free_shipping"))

    taxable = max(subtotal - discount, 0)
    if delivery == "express":
        shipping = catalog.SHIPPING["express"] if lines else 0
    elif free_shipping or taxable >= catalog.SHIPPING["free_threshold"]:
        shipping = 0
    else:
        shipping = catalog.SHIPPING["standard"] if lines else 0

    tax = int(round(taxable * catalog.TAX_RATE))
    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": taxable + tax + shipping,
        "tax_rate": int(catalog.TAX_RATE * 100),
        "free_shipping_gap": max(catalog.SHIPPING["free_threshold"] - taxable, 0),
        "promo_code": (promo_code or "").upper(),
        "promo": promo,
        "promo_applies": promo_applies,
        "delivery": delivery,
        "item_count": sum(line["quantity"] for line in lines),
    }


def cart_payload() -> dict:
    lines = cart_lines()
    totals = cart_totals(lines, session.get("promo"), session.get("delivery", "standard"))
    return {
        "count": totals["item_count"],
        "subtotal": totals["subtotal"],
        "subtotal_display": format_money(totals["subtotal"]),
        "total_display": format_money(totals["total"]),
        "items": [
            {
                "key": line["key"],
                "slug": line["slug"],
                "name": line["name"],
                "variant": line["variant"],
                "image": url_for("static", filename=f"img/{line['image']}"),
                "quantity": line["quantity"],
                "line_display": format_money(line["line_total"]),
                "price_display": format_money(line["unit_price"]),
            }
            for line in lines
        ],
    }


def wants_json() -> bool:
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
        and request.accept_mimetypes["application/json"] > request.accept_mimetypes["text/html"]
    )


def safe_next(target: str | None) -> str | None:
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/"):
        return None
    return target


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        if g.user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def wishlist_ids() -> set[int]:
    if g.user is None:
        return set()
    rows = get_db().execute("SELECT product_id FROM wishlist WHERE user_id = ?", (g.user["id"],)).fetchall()
    return {row["product_id"] for row in rows}


def validate_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", value or ""))


def clean(value: str | None, limit: int = 500) -> str:
    return (value or "").strip()[:limit]


# --------------------------------------------------------------------------- request lifecycle
@app.before_request
def prepare_request():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

    g.user = None
    user_id = session.get("user_id")
    if user_id:
        g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if g.user is None:
            session.pop("user_id", None)

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token", "")
        if not sent or not expected or not hmac.compare_digest(str(sent), str(expected)):
            if wants_json():
                return jsonify({"ok": False, "error": "Your session expired. Please refresh the page."}), 400
            return render_template(
                "error.html",
                code=400,
                title="Session expired",
                message="We could not verify that form submission. Please refresh the page and try again.",
            ), 400


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    if PRODUCTION:
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    ancestors = "'self'" if PRODUCTION else "'self' https://*.e2b.app https://*.vercel.app"
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; script-src 'self'; form-action 'self'; base-uri 'self'; "
        f"frame-ancestors {ancestors}",
    )
    return response


@app.context_processor
def inject_globals():
    cart = cart_map()
    totals = cart_totals(cart_lines(), session.get("promo"), session.get("delivery", "standard"))
    category_counts = {
        row["category"]: row["total"]
        for row in get_db().execute("SELECT category, COUNT(*) AS total FROM products GROUP BY category")
    }
    categories = [
        {**category, "count": category_counts.get(category["slug"], 0)}
        for category in catalog.CATEGORIES
    ]
    return {
        "store": catalog.STORE,
        "categories": categories,
        "cart_count": totals["item_count"],
        "cart_subtotal": totals["subtotal"],
        "money": format_money,
        "current_user": g.get("user"),
        "wishlist_ids": wishlist_ids(),
        "csrf_token": session.get("csrf_token", ""),
        "asset_version": ASSET_VERSION,
        "current_year": datetime.now(timezone.utc).year,
        "free_shipping_threshold": catalog.SHIPPING["free_threshold"],
        "order_statuses": ORDER_STATUSES,
        "promos": catalog.PROMOS,
    }


# --------------------------------------------------------------------------- storefront
@app.route("/")
def home():
    featured = product_rows("WHERE p.featured = 1", (), "p.id ASC", limit=8)
    latest = product_rows("", (), "p.id DESC", limit=3)
    newest = latest[0] if latest else None
    review_count = get_db().execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    average_rating = get_db().execute("SELECT COALESCE(AVG(rating), 0) FROM reviews").fetchone()[0]
    testimonials = rows_to_dicts(
        get_db()
        .execute(
            """
            SELECT r.*, p.name AS product_name, p.slug AS product_slug
            FROM reviews r JOIN products p ON p.id = r.product_id
            WHERE r.rating = 5
            ORDER BY r.id ASC LIMIT 3
            """
        )
        .fetchall()
    )
    return render_template(
        "index.html",
        featured=featured,
        hero_product=featured[0] if featured else newest,
        testimonials=testimonials,
        review_count=review_count,
        average_rating=average_rating,
        product_total=get_db().execute("SELECT COUNT(*) FROM products").fetchone()[0],
    )


@app.route("/shop")
def shop():
    query = clean(request.args.get("q"), 80)
    category = clean(request.args.get("category"), 40)
    sort = clean(request.args.get("sort"), 20) or "featured"
    in_stock = request.args.get("in_stock") == "1"
    try:
        min_price = int(request.args.get("min_price") or 0)
    except ValueError:
        min_price = 0
    try:
        max_price = int(request.args.get("max_price") or 0)
    except ValueError:
        max_price = 0
    try:
        page = max(1, int(request.args.get("page") or 1))
    except ValueError:
        page = 1

    clauses, params = [], []
    if query:
        clauses.append("(p.name LIKE ? OR p.summary LIKE ? OR p.description LIKE ? OR p.category LIKE ?)")
        like = f"%{query}%"
        params.extend([like, like, like, like])
    if category and category in catalog.CATEGORY_NAMES:
        clauses.append("p.category = ?")
        params.append(category)
    if min_price:
        clauses.append("p.price >= ?")
        params.append(min_price)
    if max_price:
        clauses.append("p.price <= ?")
        params.append(max_price)
    if in_stock:
        clauses.append("p.stock > 0")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    orders = {
        "featured": "p.featured DESC, p.id ASC",
        "newest": "p.id DESC",
        "price-asc": "p.price ASC",
        "price-desc": "p.price DESC",
        "rating": "rating_avg DESC, review_count DESC",
        "name": "p.name ASC",
    }
    order = orders.get(sort, orders["featured"])

    per_page = 9
    total = get_db().execute(f"SELECT COUNT(*) FROM products p {where}", tuple(params)).fetchone()[0]
    pages = max(1, -(-total // per_page))
    page = min(page, pages)
    products = product_rows(where, tuple(params), order, limit=per_page, offset=(page - 1) * per_page)

    def page_url(target_page: int) -> str:
        args = request.args.to_dict()
        args["page"] = target_page
        return url_for("shop", **args)

    def build_url(**overrides) -> str:
        """Current filters with one or more values replaced (empty removes them)."""
        args = request.args.to_dict()
        args.pop("page", None)
        args.update(overrides)
        cleaned = {key: value for key, value in args.items() if value not in (None, "", 0, False)}
        return url_for("shop", **cleaned) if cleaned else url_for("shop")

    active_category = next((c for c in catalog.CATEGORIES if c["slug"] == category), None)
    return render_template(
        "shop.html",
        products=products,
        total=total,
        product_total=get_db().execute("SELECT COUNT(*) FROM products").fetchone()[0],
        page=page,
        pages=pages,
        page_url=page_url,
        build_url=build_url,
        query=query,
        category=category,
        active_category=active_category,
        sort=sort,
        in_stock=in_stock,
        min_price=min_price,
        max_price=max_price,
    )


@app.route("/product/<slug>")
def product_detail(slug: str):
    product = get_product(slug)
    if product is None:
        abort(404)

    reviews = rows_to_dicts(
        get_db()
        .execute("SELECT * FROM reviews WHERE product_id = ? ORDER BY created_at DESC", (product["id"],))
        .fetchall()
    )
    distribution = {star: 0 for star in range(5, 0, -1)}
    for review in reviews:
        distribution[min(max(int(review["rating"]), 1), 5)] += 1
    related = product_rows("WHERE p.category = ? AND p.id != ?", (product["category"], product["id"]), "p.featured DESC, p.id ASC", limit=4)
    if len(related) < 4:
        seen = {product["id"], *(item["id"] for item in related)}
        fillers = [item for item in product_rows("", (), "p.featured DESC, p.id ASC", limit=8) if item["id"] not in seen]
        related.extend(fillers[: 4 - len(related)])

    has_reviewed = False
    if g.user:
        has_reviewed = bool(
            get_db()
            .execute("SELECT 1 FROM reviews WHERE product_id = ? AND user_id = ?", (product["id"], g.user["id"]))
            .fetchone()
        )

    return render_template(
        "product.html",
        product=product,
        reviews=reviews,
        distribution=distribution,
        review_total=len(reviews),
        related=related,
        has_reviewed=has_reviewed,
    )


# --------------------------------------------------------------------------- cart
@app.route("/cart")
def cart():
    lines = cart_lines()
    promo_code = session.get("promo")
    totals = cart_totals(lines, promo_code, session.get("delivery", "standard"))
    return render_template("cart.html", lines=lines, totals=totals, promo_code=promo_code or "")


@app.post("/cart/add")
def cart_add():
    try:
        product_id = int(request.form.get("product_id", "0"))
        quantity = max(1, min(int(request.form.get("quantity", "1")), 20))
    except ValueError:
        product_id = 0
        quantity = 1

    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        if wants_json():
            return jsonify({"ok": False, "error": "That piece is no longer available."}), 404
        flash("That piece is no longer available.", "error")
        return redirect(url_for("shop"))

    variants = json.loads(product["variants"] or "[]")
    variant = request.form.get("variant") or (variants[0] if variants else "")
    if variants and variant not in variants:
        variant = variants[0]

    if product["stock"] <= 0:
        message = "This piece is sold out — join the waitlist below."
        if wants_json():
            return jsonify({"ok": False, "error": message}), 409
        flash(message, "error")
        return redirect(url_for("product_detail", slug=product["slug"]))

    cart = cart_map()
    key = f"{product['id']}|{variant}"
    cart[key] = min(int(cart.get(key, 0)) + quantity, int(product["stock"]))
    save_cart(cart)

    if wants_json():
        payload = cart_payload()
        payload.update({"ok": True, "message": f"{product['name']} added to your bag."})
        return jsonify(payload)

    flash(f"{product['name']} added to your bag.", "success")
    return redirect(safe_next(request.form.get("next")) or url_for("cart"))


@app.post("/cart/update")
def cart_update():
    key = request.form.get("key", "")
    try:
        quantity = int(request.form.get("quantity", "0"))
    except ValueError:
        quantity = 0

    cart = cart_map()
    if key not in cart:
        return redirect(url_for("cart"))

    product_id, _ = parse_key(key)
    product = get_db().execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()
    limit = int(product["stock"]) if product else 0

    if quantity <= 0:
        cart.pop(key, None)
    else:
        cart[key] = max(1, min(quantity, limit, 20))
    save_cart(cart)

    if wants_json():
        return jsonify({"ok": True, **cart_payload()})
    return redirect(url_for("cart"))


@app.post("/cart/remove")
def cart_remove():
    key = request.form.get("key", "")
    cart = cart_map()
    removed = cart.pop(key, None)
    save_cart(cart)
    if removed:
        flash("Item removed from your bag.", "info")
    if wants_json():
        return jsonify({"ok": True, **cart_payload()})
    return redirect(url_for("cart"))


@app.post("/cart/promo")
def cart_promo():
    code = clean(request.form.get("promo_code"), 30).upper()
    lines = cart_lines()
    if not lines:
        flash("Your bag is empty.", "info")
        return redirect(url_for("cart"))

    promo = catalog.PROMOS.get(code)
    if promo is None:
        session.pop("promo", None)
        flash("That code is not valid.", "error")
        return redirect(url_for("cart"))

    subtotal = sum(line["line_total"] for line in lines)
    if subtotal < promo["min_subtotal"]:
        session.pop("promo", None)
        flash(f"{code} needs a subtotal of {format_money(promo['min_subtotal'])} or more.", "error")
        return redirect(url_for("cart"))

    session["promo"] = code
    flash(f"{code} applied — {promo['label']}.", "success")
    return redirect(url_for("cart"))


@app.post("/cart/promo/remove")
def cart_promo_remove():
    session.pop("promo", None)
    flash("Promo code removed.", "info")
    return redirect(url_for("cart"))


@app.get("/api/cart")
def api_cart():
    return jsonify(cart_payload())


# --------------------------------------------------------------------------- checkout
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    lines = cart_lines()
    if not lines:
        flash("Your bag is empty — add something beautiful first.", "info")
        return redirect(url_for("shop"))

    delivery = request.values.get("delivery_method", session.get("delivery", "standard"))
    if delivery not in DELIVERY_METHODS:
        delivery = "standard"
    session["delivery"] = delivery
    totals = cart_totals(lines, session.get("promo"), delivery)
    standard_shipping = cart_totals(lines, session.get("promo"), "standard")["shipping"]

    form = {
        "email": (g.user["email"] if g.user else ""),
        "full_name": (g.user["name"] if g.user else ""),
        "phone": "",
        "address_line": "",
        "city": "",
        "state": "",
        "postal_code": "",
        "note": "",
        "payment_method": "card",
        "delivery_method": delivery,
    }
    errors: dict[str, str] = {}

    if request.method == "POST":
        form.update({key: clean(request.form.get(key), 200) for key in form})
        form["payment_method"] = request.form.get("payment_method", "card")

        if not validate_email(form["email"]):
            errors["email"] = "Enter a valid email address."
        if len(form["full_name"]) < 2:
            errors["full_name"] = "Enter your full name."
        if not re.fullmatch(r"[0-9+\-\s()]{8,18}", form["phone"]):
            errors["phone"] = "Enter a reachable phone number."
        if len(form["address_line"]) < 6:
            errors["address_line"] = "Enter your street address."
        if len(form["city"]) < 2:
            errors["city"] = "Enter your city."
        if not re.fullmatch(r"[0-9]{5,6}", form["postal_code"]):
            errors["postal_code"] = "Enter a 6-digit PIN code."
        if form["payment_method"] not in PAYMENT_METHODS:
            errors["payment_method"] = "Choose a payment method."
        if not request.form.get("terms"):
            errors["terms"] = "Please accept the terms of sale to continue."

        if not errors:
            connection = get_db()
            try:
                for line in lines:
                    updated = connection.execute(
                        "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                        (line["quantity"], line["product_id"], line["quantity"]),
                    )
                    if updated.rowcount != 1:
                        raise ValueError(f"{line['name']} is no longer available in that quantity.")

                order_number = db.new_order_number(connection)
                cursor = connection.execute(
                    """
                    INSERT INTO orders (order_number, user_id, email, full_name, phone, address_line,
                                        city, state, postal_code, country, subtotal, discount, shipping,
                                        tax, total, promo_code, delivery_method, payment_method, note, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_number, g.user["id"] if g.user else None, form["email"], form["full_name"],
                        form["phone"], form["address_line"], form["city"], form["state"],
                        form["postal_code"], "India", totals["subtotal"], totals["discount"],
                        totals["shipping"], totals["tax"], totals["total"], totals["promo_code"],
                        form["delivery_method"], form["payment_method"], form["note"], "Processing",
                    ),
                )
                order_id = cursor.lastrowid
                for line in lines:
                    connection.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, slug, name, variant, unit_price, quantity, image)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (order_id, line["product_id"], line["slug"], line["name"], line["variant"],
                         line["unit_price"], line["quantity"], line["image"]),
                    )
                connection.commit()
            except ValueError as exc:
                connection.rollback()
                flash(str(exc), "error")
                return render_template("checkout.html", lines=lines, totals=totals, standard_shipping=standard_shipping, form=form, errors=errors), 409
            except sqlite3.Error:
                connection.rollback()
                app.logger.exception("checkout failed")
                flash("We could not complete that order. Please try again.", "error")
                return render_template("checkout.html", lines=lines, totals=totals, standard_shipping=standard_shipping, form=form, errors=errors), 500

            save_cart({})
            session.pop("promo", None)
            session["last_order"] = order_number
            return redirect(url_for("order_confirmation", order_number=order_number))

    return render_template(
        "checkout.html",
        lines=lines,
        totals=totals,
        standard_shipping=standard_shipping,
        form=form,
        errors=errors,
    )


@app.route("/order/<order_number>")
def order_confirmation(order_number: str):
    connection = get_db()
    order = connection.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
    if order is None:
        abort(404)

    allowed = (
        session.get("last_order") == order_number
        or (g.user and order["user_id"] == g.user["id"])
        or (g.user and g.user["role"] == "admin")
    )
    if not allowed:
        flash("Sign in to view that order, or track it with your order number and email.", "info")
        return redirect(url_for("track", order=order_number))

    items = rows_to_dicts(connection.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall())
    timeline = ORDER_STATUSES[:4]
    current_index = timeline.index(order["status"]) if order["status"] in timeline else 0
    return render_template(
        "order.html",
        order=order,
        items=items,
        timeline=timeline,
        current_index=current_index,
        payment_label=PAYMENT_METHODS.get(order["payment_method"], order["payment_method"]),
        delivery_label=DELIVERY_METHODS.get(order["delivery_method"], order["delivery_method"]),
    )


@app.route("/track", methods=["GET", "POST"])
def track():
    lookup = None
    items: list[dict] = []
    error = None

    initial = clean(request.args.get("order"), 20)
    if request.method == "POST":
        number = clean(request.form.get("order_number"), 20).upper()
        email = clean(request.form.get("email"), 120).lower()
        connection = get_db()
        lookup = connection.execute("SELECT * FROM orders WHERE order_number = ?", (number,)).fetchone()
        if lookup is None or lookup["email"].lower() != email:
            lookup, error = None, "We could not find an order with that number and email."
        else:
            items = rows_to_dicts(connection.execute("SELECT * FROM order_items WHERE order_id = ?", (lookup["id"],)).fetchall())

    timeline = ORDER_STATUSES[:4]
    current_index = timeline.index(lookup["status"]) if lookup and lookup["status"] in timeline else 0
    return render_template(
        "track.html",
        lookup=lookup,
        items=items,
        error=error,
        initial=initial,
        timeline=timeline,
        current_index=current_index,
    )


# --------------------------------------------------------------------------- accounts
@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("account"))

    error = None
    email = ""
    if request.method == "POST":
        email = clean(request.form.get("email"), 120).lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "That email and password combination does not match our records."
        else:
            session.permanent = True
            session["user_id"] = user["id"]
            session.pop("csrf_token", None)
            flash(f"Welcome back, {user['name'].split()[0]}.", "success")
            destination = safe_next(request.args.get("next") or request.form.get("next"))
            return redirect(destination or url_for("account"))

    return render_template("login.html", error=error, email=email)


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("account"))

    errors: dict[str, str] = {}
    form = {"name": "", "email": ""}
    if request.method == "POST":
        form["name"] = clean(request.form.get("name"), 120)
        form["email"] = clean(request.form.get("email"), 120).lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(form["name"]) < 2:
            errors["name"] = "Tell us your name."
        if not validate_email(form["email"]):
            errors["email"] = "Enter a valid email address."
        if len(password) < 8:
            errors["password"] = "Use at least 8 characters."
        if password != confirm:
            errors["confirm_password"] = "Passwords do not match."
        if request.form.get("website"):
            errors["name"] = "Something went wrong. Please try again."

        if not errors:
            connection = get_db()
            existing = connection.execute("SELECT 1 FROM users WHERE lower(email) = ?", (form["email"],)).fetchone()
            if existing:
                errors["email"] = "An account with that email already exists."
            else:
                cursor = connection.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'customer')",
                    (form["name"], form["email"], generate_password_hash(password)),
                )
                connection.commit()
                session.permanent = True
                session["user_id"] = cursor.lastrowid
                session.pop("csrf_token", None)
                flash("Your account is ready. Welcome to Aurum & Ivy.", "success")
                return redirect(safe_next(request.args.get("next")) or url_for("account"))

    return render_template("register.html", errors=errors, form=form)


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("home"))


@app.route("/account")
@login_required
def account():
    connection = get_db()
    orders = rows_to_dicts(
        connection.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (g.user["id"],)).fetchall()
    )
    for order in orders:
        order["line_items"] = rows_to_dicts(
            connection.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
        )
    wishlist = product_rows(
        "WHERE p.id IN (SELECT product_id FROM wishlist WHERE user_id = ?)",
        (g.user["id"],),
        "p.id ASC",
    )
    spent = sum(order["total"] for order in orders if order["status"] != "Cancelled")
    return render_template(
        "account.html",
        orders=orders,
        wishlist=wishlist,
        spent=spent,
        address=orders[0] if orders else None,
    )


@app.post("/orders/<int:order_id>/reorder")
@login_required
def reorder(order_id: int):
    connection = get_db()
    order = connection.execute(
        "SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, g.user["id"])
    ).fetchone()
    if order is None:
        abort(404)

    lines = connection.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    products = {row["id"]: row for row in connection.execute("SELECT * FROM products").fetchall()}
    cart = cart_map()
    added = 0
    for line in lines:
        product = products.get(line["product_id"])
        if product is None or product["stock"] <= 0:
            continue
        key = f"{product['id']}|{line['variant']}"
        quantity = min(int(line["quantity"]), int(product["stock"]))
        cart[key] = min(int(cart.get(key, 0)) + quantity, int(product["stock"]))
        added += quantity

    save_cart(cart)
    if added:
        flash(f"{added} piece{'s' if added != 1 else ''} from order {order['order_number']} added to your bag.", "success")
        return redirect(url_for("cart"))

    flash("Those pieces are no longer in stock.", "error")
    return redirect(url_for("account"))


@app.post("/wishlist/toggle")
def wishlist_toggle():
    slug = clean(request.form.get("slug"), 80)
    product = get_db().execute("SELECT id, slug FROM products WHERE slug = ?", (slug,)).fetchone()
    if product is None:
        abort(404)
    if g.user is None:
        flash("Sign in to save pieces to your wishlist.", "info")
        return redirect(url_for("login", next=url_for("product_detail", slug=slug)))

    connection = get_db()
    existing = connection.execute(
        "SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?", (g.user["id"], product["id"])
    ).fetchone()
    if existing:
        connection.execute("DELETE FROM wishlist WHERE id = ?", (existing["id"],))
        message, saved = "Removed from your wishlist.", False
    else:
        connection.execute("INSERT INTO wishlist (user_id, product_id) VALUES (?, ?)", (g.user["id"], product["id"]))
        message, saved = "Saved to your wishlist.", True
    connection.commit()

    if wants_json():
        return jsonify({"ok": True, "saved": saved, "message": message})
    flash(message, "success")
    return redirect(safe_next(request.form.get("next")) or url_for("product_detail", slug=slug))


@app.post("/product/<slug>/review")
def add_review(slug: str):
    product = get_db().execute("SELECT id FROM products WHERE slug = ?", (slug,)).fetchone()
    if product is None:
        abort(404)
    if g.user is None:
        flash("Sign in to write a review.", "info")
        return redirect(url_for("login", next=url_for("product_detail", slug=slug)))

    try:
        rating = int(request.form.get("rating", "0"))
    except ValueError:
        rating = 0
    if rating not in {1, 2, 3, 4, 5}:
        flash("Choose a rating between one and five stars.", "error")
        return redirect(url_for("product_detail", slug=slug) + "#reviews")

    connection = get_db()
    if connection.execute(
        "SELECT 1 FROM reviews WHERE product_id = ? AND user_id = ?", (product["id"], g.user["id"])
    ).fetchone():
        flash("You have already reviewed this piece.", "info")
        return redirect(url_for("product_detail", slug=slug) + "#reviews")

    connection.execute(
        "INSERT INTO reviews (product_id, user_id, author, rating, title, body) VALUES (?, ?, ?, ?, ?, ?)",
        (product["id"], g.user["id"], g.user["name"], rating,
         clean(request.form.get("title"), 120), clean(request.form.get("body"), 1200)),
    )
    connection.commit()
    flash("Thank you — your review is live.", "success")
    return redirect(url_for("product_detail", slug=slug) + "#reviews")


@app.post("/newsletter")
def newsletter():
    email = clean(request.form.get("email"), 120).lower()
    if not validate_email(email):
        flash("Enter a valid email address to subscribe.", "error")
        return redirect(safe_next(request.form.get("next")) or url_for("home"))
    connection = get_db()
    connection.execute("INSERT OR IGNORE INTO newsletter (email) VALUES (?)", (email,))
    connection.commit()
    flash("You are on the list — look out for The Edit.", "success")
    return redirect(safe_next(request.form.get("next")) or url_for("home"))


# --------------------------------------------------------------------------- admin
@app.route("/admin")
@admin_required
def admin():
    connection = get_db()
    stats = {
        "revenue": connection.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'Cancelled'").fetchone()[0],
        "orders": connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "customers": connection.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'").fetchone()[0],
        "products": connection.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "low_stock": connection.execute("SELECT COUNT(*) FROM products WHERE stock <= 3").fetchone()[0],
        "subscribers": connection.execute("SELECT COUNT(*) FROM newsletter").fetchone()[0],
    }
    recent_orders = rows_to_dicts(connection.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 12").fetchall())
    inventory = rows_to_dicts(connection.execute("SELECT * FROM products ORDER BY stock ASC, name ASC").fetchall())
    best_sellers = rows_to_dicts(
        connection.execute(
            """
            SELECT oi.name, SUM(oi.quantity) AS units, SUM(oi.quantity * oi.unit_price) AS revenue
            FROM order_items oi JOIN orders o ON o.id = oi.order_id
            WHERE o.status != 'Cancelled'
            GROUP BY oi.name ORDER BY units DESC LIMIT 5
            """
        ).fetchall()
    )
    return render_template(
        "admin.html",
        stats=stats,
        recent_orders=recent_orders,
        inventory=inventory,
        best_sellers=best_sellers,
    )


@app.post("/admin/orders/<int:order_id>/status")
@admin_required
def admin_update_status(order_id: int):
    status = request.form.get("status", "")
    if status not in ORDER_STATUSES:
        flash("Unknown status.", "error")
        return redirect(url_for("admin"))
    connection = get_db()
    order = connection.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order is None:
        abort(404)
    connection.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    connection.commit()
    flash(f"Order marked as {status.lower()}.", "success")
    return redirect(url_for("admin"))


@app.post("/admin/products/<int:product_id>/stock")
@admin_required
def admin_update_stock(product_id: int):
    try:
        stock = max(0, min(int(request.form.get("stock", "0")), 999))
    except ValueError:
        stock = 0
    connection = get_db()
    connection.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
    connection.commit()
    flash("Inventory updated.", "success")
    return redirect(url_for("admin"))


# --------------------------------------------------------------------------- meta
@app.get("/health")
def health():
    assets = {
        name: (BASE_DIR / "static" / name).is_file()
        for name in ("css/store.css", "js/store.js", "img/meridian-headphones.jpg")
    }
    try:
        get_db().execute("SELECT 1").fetchone()
    except sqlite3.Error:
        app.logger.exception("health check failed")
        return jsonify({"status": "error", "assets": assets}), 503
    return jsonify(
        {
            "status": "ok",
            "database": db.database_path(),
            "assets": assets,
            "asset_version": ASSET_VERSION,
        }
    )


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, title="Something was missing",
                           message="That request could not be processed. Please try again."), 400


@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html", code=403, title="Not for your eyes",
                           message="You do not have access to that part of the house."), 403


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, title="Page not found",
                           message="The page you were looking for has moved, or never existed."), 404


@app.errorhandler(413)
def too_large(error):
    return render_template("error.html", code=413, title="That is too large",
                           message="The request was larger than we can accept."), 413


@app.errorhandler(500)
def server_error(error):
    return render_template("error.html", code=500, title="A stitch came loose",
                           message="Something went wrong on our side. Please try again in a moment."), 500


# --------------------------------------------------------------------------- bootstrap
db.init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
