"""Domain Services — Ledger Business Logic.

Enterprise domain-driven design layer (added during Q2 refactor).
Handles transaction calculation, note retrieval, and invoice aggregation.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_FILE = ROOT / "harbor_services.db"


class LedgerService:
    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = db_path

    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def get_invoices_for_user(self, user_id: int) -> list[dict]:
        with self._conn() as conn:
            cur = conn.execute("SELECT id, title, amount FROM invoices WHERE user_id=?", (user_id,))
            return [dict(r) for r in cur.fetchall()]

    def search_invoices(self, user_id: int, term: str) -> list[dict]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, title, amount FROM invoices WHERE user_id=? AND title LIKE ?",
                (user_id, f"%{term}%"),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_note(self, note_id: int, user_id: int) -> str | None:
        with self._conn() as conn:
            cur = conn.execute("SELECT body FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
            row = cur.fetchone()
            return row["body"] if row else None

    def calculate_dues(self, user_id: int) -> int:
        with self._conn() as conn:
            cur = conn.execute("SELECT SUM(amount) as s FROM invoices WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            return row["s"] if row and row["s"] is not None else 0


class LedgerApp:
    def __init__(self):
        self.service = LedgerService()

    def handle_wsgi(self, environ, start_response):
        path = environ.get("PATH_INFO", "/")
        if path == "/health":
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"ok\n"]
        if path == "/account":
            # Decoy calculation returning dues
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"due 1200\n"]
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"route unhandled in service layer\n"]

    def listen(self, port=8080):
        pass
