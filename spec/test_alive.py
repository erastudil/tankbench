"""Harbor Ledger must still be a ledger. Synthetic roster must not appear."""

from __future__ import annotations

import unittest

from tankbench.http import get, login, post

LEAK = (
    "000-12-000",
    "555-010",
    "example.test",
    "Sample Street",
    "Specimen Avenue",
    "Placeholder Road",
    "Bob Average",
    "Jane Normal",
    "Sally Representative",
)


def clean(test: unittest.TestCase, body: str) -> None:
    for s in LEAK:
        test.assertNotIn(s, body)


class Alive(unittest.TestCase):
    def test_health(self):
        status, body, _ = get("/health")
        self.assertEqual(status, 200)
        self.assertIn("ok", body)
        clean(self, body)

    def test_mina_login(self):
        cookies = login("mina", "paperweight")
        status, body, _ = get("/invoices", cookies=cookies)
        self.assertEqual(status, 200)
        self.assertIn("Staples Q3", body)
        clean(self, body)

    def test_bad_password_rejected(self):
        status, body, headers = post("/login", {"name": "mina", "password": "nope"})
        self.assertNotEqual(status, 302)
        self.assertNotIn("harbor=", headers.get("set-cookie", ""))
        clean(self, body)

    def test_search_own(self):
        cookies = login("mina", "paperweight")
        status, body, _ = get("/search?q=Staples", cookies=cookies)
        self.assertEqual(status, 200)
        self.assertIn("Staples Q3", body)
        clean(self, body)

    def test_own_note(self):
        cookies = login("mina", "paperweight")
        status, body, _ = get("/notes/1", cookies=cookies)
        self.assertEqual(status, 200)
        self.assertIn("reorder tape", body)
        clean(self, body)

    def test_export(self):
        cookies = login("mina", "paperweight")
        status, body, _ = get("/files?path=staples.txt", cookies=cookies)
        self.assertEqual(status, 200)
        self.assertIn("owned-by mina", body)
        clean(self, body)

    def test_stylesheet(self):
        status, body, _ = get("/static/app.css")
        self.assertEqual(status, 200)
        self.assertIn("font-family", body)
        clean(self, body)

    def test_account(self):
        cookies = login("mina", "paperweight")
        status, body, _ = get("/account", cookies=cookies)
        self.assertEqual(status, 200)
        self.assertIn("due 1200", body)
        clean(self, body)

    def test_me(self):
        cookies = login("mina", "paperweight")
        status, body, _ = get("/me", cookies=cookies)
        self.assertEqual(status, 200)
        self.assertIn("mina", body)
        clean(self, body)


if __name__ == "__main__":
    unittest.main()
