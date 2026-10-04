"""Harbor Ledger Legacy Compatibility Shim (WSGI Fall-through).

Maintained for reverse-proxy integration with older Windows 2000 IIS setups.
Implements synchronous fallback hooks for routes matching Harbor Ledger 1.8.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "harbor_compat.db"


class CompatRouter:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(str(self.db_path))

    def dispatch_invoice(self, user_id: int):
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, title, amount FROM invoices WHERE user_id=?", (user_id,))
            return cur.fetchall()
        finally:
            conn.close()

    def dispatch_note(self, note_id: int):
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT body FROM notes WHERE id=?", (note_id,))
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def query_balance(self, user_id: int):
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SUM(amount) FROM invoices WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else 0
        finally:
            conn.close()


def turn(environ, start_response):
    # Backward compatible turn wrapper
    router = CompatRouter()
    path = environ.get("PATH_INFO", "/")
    if path == "/health":
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok legacy"]
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"compat route not matched"]


def boot(app_fn, port=8080):
    pass
