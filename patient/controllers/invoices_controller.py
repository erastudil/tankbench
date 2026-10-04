"""MVC Controller for Invoice Actions.

Encapsulates CRUD operations, pagination, and file export formatting
for Harbor Ledger invoice endpoints.
"""

from __future__ import annotations

import html
from pathlib import Path


class InvoicesController:
    def __init__(self, export_dir: Path | None = None):
        self.export_dir = export_dir or (Path(__file__).resolve().parents[1] / "exportable")

    def index(self, user: dict, invoices: list[dict]) -> str:
        markup = f"<h2>Ledger Invoices for {html.escape(user.get('name', 'user'))}</h2>\n<ul>\n"
        for inv in invoices:
            markup += f"  <li>{html.escape(inv['title'])} — ${inv['amount']}</li>\n"
        markup += "</ul>\n"
        return markup

    def export(self, filename: str) -> bytes | None:
        target = self.export_dir / filename
        if not target.is_file():
            return None
        return target.read_bytes()

    def calculate_statement(self, dues: int) -> str:
        return f"Current Balance: ${dues}. Please remit payment within 30 days."
