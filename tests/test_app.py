"""End-to-end tests for the Aurum & Ivy storefront.

Run from the repository root:  python -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TMP_DIR = tempfile.mkdtemp(prefix="aurum-ivy-tests-")
os.environ["STORE_DATABASE"] = str(Path(TMP_DIR) / "test.db")
os.environ["SECRET_KEY"] = "test-secret-key"

import app as store  # noqa: E402
import catalog  # noqa: E402
import db  # noqa: E402

CHECKOUT_DATA = {
    "email": "buyer@example.com",
    "full_name": "Test Buyer",
    "phone": "9820011223",
    "address_line": "12 Test Street, Fort",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "note": "Leave with the concierge",
    "payment_method": "card",
    "delivery_method": "standard",
    "terms": "1",
}


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        db.reset_db()
        store.app.config.update(TESTING=True)
        self.client = store.app.test_client()

    # ------------------------------------------------------------------ utils
    def token(self) -> str:
        with self.client.session_transaction() as sess:
            if not sess.get("csrf_token"):
                sess["csrf_token"] = "test-csrf-token"
            return sess["csrf_token"]

    def post(self, path, data=None, follow=False, **kwargs):
        payload = dict(data or {})
        payload.setdefault("csrf_token", self.token())
        return self.client.post(path, data=payload, follow_redirects=follow, **kwargs)

    def login(self, email="demo@aurumivy.com", password="demo1234"):
        return self.post("/login", {"email": email, "password": password})

    def product(self, slug="meridian-anc-headphones"):
        connection = db.connect()
        try:
            row = connection.execute("SELECT * FROM products WHERE slug = ?", (slug,)).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def add_to_cart(self, slug="meridian-anc-headphones", quantity=1, variant=None):
        product = self.product(slug)
        return self.post(
            "/cart/add",
            {
                "product_id": product["id"],
                "quantity": str(quantity),
                "variant": variant or "Ivory / Brass",
                "next": "/cart",
            },
        )

    def place_order(self):
        self.add_to_cart()
        response = self.post("/checkout", CHECKOUT_DATA)
        return response.headers.get("Location", "")


# --------------------------------------------------------------------------- pages
class PublicPagesTest(StoreTestCase):
    def test_home_renders_storefront(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn("Aurum", body)
        self.assertIn("Meridian ANC Headphones", body)
        self.assertIn("The Winter Edit", body)

    def test_shop_lists_every_piece(self):
        body = ""
        for page in (1, 2):
            response = self.client.get(f"/shop?page={page}")
            self.assertEqual(response.status_code, 200)
            body += response.data.decode()
        for product in catalog.PRODUCTS:
            self.assertIn(product["name"], body)

    def test_shop_filters_by_category(self):
        response = self.client.get("/shop?category=timepieces")
        body = response.data.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Solstice Automatic Watch", body)
        self.assertNotIn("Nocturne Cashmere Throw", body)

    def test_shop_search_matches_description(self):
        response = self.client.get("/shop?q=cashmere")
        body = response.data.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Nocturne Cashmere Throw", body)
        self.assertNotIn("Voyage Insulated Flask", body)

    def test_shop_sort_and_pagination_are_safe(self):
        for query in ("?sort=price-asc", "?sort=price-desc", "?sort=rating", "?page=99", "?page=abc"):
            response = self.client.get("/shop" + query)
            self.assertEqual(response.status_code, 200, query)

    def test_product_detail(self):
        response = self.client.get("/product/meridian-anc-headphones")
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn("Meridian ANC Headphones", body)
        self.assertIn("Ivory / Brass", body)
        self.assertIn("Add to bag", body)

    def test_unknown_product_is_404(self):
        self.assertEqual(self.client.get("/product/not-a-real-piece").status_code, 404)
        response = self.client.get("/nowhere")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Page not found", response.data.decode())

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_money_filter_uses_indian_grouping(self):
        self.assertEqual(store.format_money(124900), "\u20b91,24,900")
        self.assertEqual(store.format_money(999), "\u20b9999")
        self.assertEqual(store.format_money(0), "\u20b90")
        self.assertEqual(store.format_money(-4500), "-\u20b94,500")

    def test_security_headers_are_present(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        csp = response.headers["Content-Security-Policy"]
        self.assertIn("frame-ancestors", csp)
        self.assertIn("default-src 'self'", csp)
        self.assertEqual(response.headers["Referrer-Policy"], "strict-origin-when-cross-origin")

    def test_csrf_token_is_required(self):
        response = self.client.post("/cart/add", data={"product_id": 1})
        self.assertEqual(response.status_code, 400)


# ----------------------------------------------------------------------- cart
class CartTest(StoreTestCase):
    def test_add_to_cart_then_see_it(self):
        response = self.add_to_cart()
        self.assertEqual(response.status_code, 302)
        page = self.client.get("/cart")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Meridian ANC Headphones", page.data.decode())
        self.assertIn("Ivory / Brass", page.data.decode())

    def test_ajax_add_returns_cart_payload(self):
        product = self.product()
        response = self.post(
            "/cart/add",
            {"product_id": product["id"], "quantity": "2", "variant": "Obsidian / Brass"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["subtotal"], product["price"] * 2)
        self.assertEqual(len(payload["items"]), 1)

    def test_quantity_cannot_exceed_stock(self):
        product = self.product("fold-leather-cardholder")  # seeded with 2 in stock
        self.post("/cart/add", {"product_id": product["id"], "quantity": "10", "variant": "Chestnut"})
        line = self.client.get("/api/cart").get_json()["items"][0]
        self.assertEqual(line["quantity"], product["stock"])

    def test_update_quantity_and_remove(self):
        self.add_to_cart(quantity=1)
        key = f"{self.product()['id']}|Ivory / Brass"
        self.post("/cart/update", {"key": key, "quantity": "3"})
        self.assertEqual(self.client.get("/api/cart").get_json()["count"], 3)
        self.post("/cart/update", {"key": key, "quantity": "1"})
        self.assertEqual(self.client.get("/api/cart").get_json()["count"], 1)
        self.post("/cart/remove", {"key": key})
        self.assertEqual(self.client.get("/api/cart").get_json()["count"], 0)

    def test_sold_out_product_is_refused(self):
        product = self.product()
        connection = db.connect()
        connection.execute("UPDATE products SET stock = 0 WHERE id = ?", (product["id"],))
        connection.commit()
        connection.close()
        response = self.post(
            "/cart/add",
            {"product_id": product["id"], "quantity": "1"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.get_json()["ok"])

    def test_promo_code_applies_and_rejects(self):
        self.add_to_cart()
        self.post("/cart/promo", {"promo_code": "WELCOME10"})
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("promo"), "WELCOME10")
        page = self.client.get("/cart").data.decode()
        self.assertIn("WELCOME10", page)

        self.post("/cart/promo", {"promo_code": "NOTACODE"})
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("promo"))

    def test_promo_minimum_is_enforced(self):
        self.add_to_cart("voyage-insulated-flask")  # 3,200 — below AURUM15's 15,000 floor
        self.post("/cart/promo", {"promo_code": "AURUM15"})
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("promo"))

# ------------------------------------------------------------------ checkout
class CheckoutTest(StoreTestCase):
    def test_empty_cart_redirects_to_shop(self):
        response = self.client.get("/checkout")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/shop", response.headers["Location"])

    def test_validation_errors_are_shown(self):
        self.add_to_cart()
        response = self.post("/checkout", {"email": "nope", "full_name": "", "phone": "1"})
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn("Enter a valid email address.", body)
        self.assertIn("Enter your full name.", body)

    def test_terms_must_be_accepted(self):
        self.add_to_cart()
        data = dict(CHECKOUT_DATA)
        data.pop("terms")
        response = self.post("/checkout", data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please accept the terms of sale", response.data.decode())

    def test_place_order_creates_order_and_decrements_stock(self):
        before = self.product()["stock"]
        location = self.place_order()
        self.assertIn("/order/AI-", location)

        order_number = location.rsplit("/", 1)[-1]
        connection = db.connect()
        order = connection.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
        items = connection.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
        connection.close()

        self.assertIsNotNone(order)
        self.assertEqual(order["email"], CHECKOUT_DATA["email"])
        self.assertEqual(order["status"], "Processing")
        self.assertEqual(len(items), 1)
        self.assertEqual(self.product()["stock"], before - 1)
        self.assertEqual(self.client.get("/api/cart").get_json()["count"], 0)

    def test_confirmation_seen_by_buyer_only(self):
        location = self.place_order()
        page = self.client.get(location)
        self.assertEqual(page.status_code, 200)
        self.assertIn("Thank you, Test.", page.data.decode())

        stranger = store.app.test_client()
        blocked = stranger.get(location)
        self.assertEqual(blocked.status_code, 302)
        self.assertIn("/track", blocked.headers["Location"])

    def test_totals_include_tax_and_delivery(self):
        lines = []
        product = self.product()
        lines.append({"line_total": product["price"], "quantity": 1, "unit_price": product["price"]})
        totals = store.cart_totals(lines, None, "standard")
        self.assertEqual(totals["subtotal"], product["price"])
        self.assertEqual(totals["shipping"], 0)  # above the free-delivery threshold
        self.assertEqual(totals["tax"], int(round(product["price"] * catalog.TAX_RATE)))
        self.assertEqual(totals["total"], product["price"] + totals["tax"])

    def test_express_delivery_adds_charge(self):
        product = self.product()
        lines = [{"line_total": product["price"], "quantity": 1, "unit_price": product["price"]}]
        totals = store.cart_totals(lines, None, "express")
        self.assertEqual(totals["shipping"], catalog.SHIPPING["express"])

    def test_track_order(self):
        location = self.place_order()
        number = location.rsplit("/", 1)[-1]
        response = self.post("/track", {"order_number": number, "email": CHECKOUT_DATA["email"]})
        self.assertEqual(response.status_code, 200)
        self.assertIn(number, response.data.decode())

    def test_track_rejects_wrong_email(self):
        location = self.place_order()
        number = location.rsplit("/", 1)[-1]
        response = self.post("/track", {"order_number": number, "email": "someone@else.com"})
        self.assertIn("could not find an order", response.data.decode())


# -------------------------------------------------------------------- accounts
class AccountTest(StoreTestCase):
    def test_register_then_see_account(self):
        response = self.post(
            "/register",
            {
                "name": "New Customer",
                "email": "new@example.com",
                "password": "supersecret1",
                "confirm_password": "supersecret1",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("New Customer", response.data.decode())

    def test_register_rejects_duplicate_email(self):
        self.post(
            "/register",
            {"name": "First Attempt", "email": "taken@example.com", "password": "password12", "confirm_password": "password12"},
        )
        self.post("/logout")
        response = self.post(
            "/register",
            {"name": "Second Attempt", "email": "taken@example.com", "password": "password12", "confirm_password": "password12"},
        )
        self.assertIn("already exists", response.data.decode())

    def test_register_rejects_short_password(self):
        response = self.post(
            "/register",
            {"name": "C", "email": "c@example.com", "password": "short", "confirm_password": "short"},
        )
        self.assertIn("at least 8 characters", response.data.decode())

    def test_login_and_logout(self):
        response = self.login()
        self.assertEqual(response.status_code, 302)
        account = self.client.get("/account")
        self.assertEqual(account.status_code, 200)
        self.assertIn("Demo Customer", account.data.decode())

        self.post("/logout")
        self.assertEqual(self.client.get("/account").status_code, 302)

    def test_login_rejects_bad_password(self):
        response = self.post("/login", {"email": "demo@aurumivy.com", "password": "wrong-password"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("does not match our records", response.data.decode())

    def test_wishlist_requires_login_then_toggles(self):
        response = self.post("/wishlist/toggle", {"slug": "halo-brass-desk-lamp"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        self.login()
        self.post("/wishlist/toggle", {"slug": "halo-brass-desk-lamp"})
        connection = db.connect()
        saved = connection.execute("SELECT COUNT(*) FROM wishlist").fetchone()[0]
        connection.close()
        self.assertEqual(saved, 1)

        page = self.client.get("/account").data.decode()
        self.assertIn("Halo Brass Desk Lamp", page)

        self.post("/wishlist/toggle", {"slug": "halo-brass-desk-lamp"})
        connection = db.connect()
        saved = connection.execute("SELECT COUNT(*) FROM wishlist").fetchone()[0]
        connection.close()
        self.assertEqual(saved, 0)

    def test_review_is_published_once(self):
        self.login()
        self.post("/product/solstice-automatic-watch/review", {"rating": "5", "title": "Superb", "body": "A quiet joy on the wrist."})
        page = self.client.get("/product/solstice-automatic-watch").data.decode()
        self.assertIn("A quiet joy on the wrist.", page)
        self.assertIn("Demo Customer", page)

        self.post("/product/solstice-automatic-watch/review", {"rating": "5", "title": "Again", "body": "duplicate"})
        page = self.client.get("/product/solstice-automatic-watch").data.decode()
        self.assertNotIn("duplicate", page)

    def test_newsletter_signup(self):
        self.post("/newsletter", {"email": "reader@example.com"})
        connection = db.connect()
        count = connection.execute("SELECT COUNT(*) FROM newsletter WHERE email = ?", ("reader@example.com",)).fetchone()[0]
        connection.close()
        self.assertEqual(count, 1)

    def test_reorder_fills_bag(self):
        self.login()
        connection = db.connect()
        order = connection.execute("SELECT * FROM orders WHERE user_id = (SELECT id FROM users WHERE email = ?)", ("demo@aurumivy.com",)).fetchone()
        connection.close()
        response = self.post(f"/orders/{order['id']}/reorder")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/cart", response.headers["Location"])
        self.assertGreater(self.client.get("/api/cart").get_json()["count"], 0)


# ----------------------------------------------------------------------- admin
class AdminTest(StoreTestCase):
    def test_admin_requires_admin_role(self):
        self.assertEqual(self.client.get("/admin").status_code, 302)
        self.login()
        self.assertEqual(self.client.get("/admin").status_code, 403)

    def test_admin_dashboard_and_status_update(self):
        self.login("admin@aurumivy.com", "admin1234")
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn("Atelier dashboard", body)
        self.assertIn("AI-100241", body)

        connection = db.connect()
        order = connection.execute("SELECT * FROM orders ORDER BY id LIMIT 1").fetchone()
        connection.close()
        self.post(f"/admin/orders/{order['id']}/status", {"status": "Shipped"})
        connection = db.connect()
        status = connection.execute("SELECT status FROM orders WHERE id = ?", (order["id"],)).fetchone()[0]
        connection.close()
        self.assertEqual(status, "Shipped")

    def test_admin_updates_stock(self):
        self.login("admin@aurumivy.com", "admin1234")
        product = self.product()
        self.post(f"/admin/products/{product['id']}/stock", {"stock": "17"})
        self.assertEqual(self.product()["stock"], 17)


# ------------------------------------------------------------------------ data
class SeedDataTest(StoreTestCase):
    def test_seed_is_idempotent(self):
        db.init_db()
        db.init_db()
        connection = db.connect()
        products = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        reviews = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        connection.close()
        self.assertEqual(products, len(catalog.PRODUCTS))
        self.assertEqual(reviews, len(catalog.REVIEWS))

    def test_every_product_is_reachable(self):
        for product in catalog.PRODUCTS:
            response = self.client.get(f"/product/{product['slug']}")
            self.assertEqual(response.status_code, 200, product["slug"])

    def test_categories_all_have_products(self):
        totals = {}
        connection = db.connect()
        for row in connection.execute("SELECT category, COUNT(*) AS total FROM products GROUP BY category"):
            totals[row["category"]] = row["total"]
        connection.close()
        for category in catalog.CATEGORIES:
            self.assertIn(category["slug"], totals, category["slug"])
            self.assertGreater(totals[category["slug"]], 0)


if __name__ == "__main__":
    unittest.main()
