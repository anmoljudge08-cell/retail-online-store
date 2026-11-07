from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import app as store


class StorefrontTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        store.app.config.update(
            TESTING=True,
            DATABASE=str(Path(self.temp_dir.name) / "test.db"),
            SECRET_KEY="test-secret",
        )
        store.init_db()
        self.client = store.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_home_and_catalog_search_and_category(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Good things for the way you live", response.data)
        self.assertIn(b"Aurora Wireless Headphones", response.data)
        search = self.client.get("/catalog?q=wireless")
        self.assertEqual(search.status_code, 200)
        self.assertIn(b"Aurora Wireless Headphones", search.data)
        self.assertNotIn(b"Terra Coffee Grinder", search.data)
        category = self.client.get("/catalog?category=Kitchen")
        self.assertEqual(category.status_code, 200)
        self.assertIn(b"Terra Coffee Grinder", category.data)
        self.assertNotIn(b"Summit Smart Watch", category.data)

    def test_registration_login_and_password_hash(self):
        response = self.client.post("/register", data={
            "name": "Taylor Store",
            "email": "taylor@example.test",
            "password": "strong-demo-password",
            "confirm_password": "strong-demo-password",
        })
        self.assertEqual(response.status_code, 302)
        with store.get_db() as connection:
            row = connection.execute("SELECT password_hash FROM users WHERE email = ?", ("taylor@example.test",)).fetchone()
        self.assertIsNotNone(row)
        self.assertNotEqual(row["password_hash"], "strong-demo-password")
        self.client.post("/logout")
        login = self.client.post("/login", data={"email": "taylor@example.test", "password": "strong-demo-password"})
        self.assertEqual(login.status_code, 302)
        self.assertEqual(self.client.get("/checkout").status_code, 302)

    def test_cart_quantities_and_server_price(self):
        self.client.post("/add_to_cart/1", data={"quantity": "2"})
        response = self.client.get("/cart")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"₹2,998", response.data)
        with self.client.session_transaction() as session:
            session["cart"]["1"]["price"] = 1
        response = self.client.get("/cart")
        self.assertIn(b"₹2,998", response.data)
        self.client.post("/cart", data={"action": "update", "item_id": "1", "quantity": "3"})
        self.assertIn(b"₹4,497", self.client.get("/cart").data)
        self.client.post("/cart", data={"action": "remove", "item_id": "1"})
        self.assertIn(b"Your cart is empty", self.client.get("/cart").data)

    def test_checkout_requires_login_then_records_demo_order(self):
        self.client.post("/add_to_cart/2", data={"quantity": "1"})
        self.assertEqual(self.client.get("/checkout").status_code, 302)
        self.client.post("/register", data={
            "name": "Demo Buyer",
            "email": "buyer@example.test",
            "password": "strong-demo-password",
            "confirm_password": "strong-demo-password",
        })
        response = self.client.post("/checkout", data={"address": "123 Demo Road"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No payment has been processed", response.data)
        self.assertIn(b"RS-", response.data)
        with store.get_db() as connection:
            order = connection.execute("SELECT total, address FROM orders").fetchone()
        self.assertEqual(order["total"], 2199)
        self.assertEqual(order["address"], "123 Demo Road")
        self.assertIn(b"Your cart is empty", self.client.get("/cart").data)

    def test_routes_and_legacy_page(self):
        self.assertEqual(self.client.get("/health").json, {"status": "ok"})
        self.assertEqual(self.client.get("/legacy").status_code, 200)
        self.assertEqual(self.client.get("/login").status_code, 200)
        self.assertEqual(self.client.get("/register").status_code, 200)


if __name__ == "__main__":
    unittest.main()
