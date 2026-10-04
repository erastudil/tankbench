"""Accounting Tax & Tariff Calculator Module.

Legacy arithmetic verification subsystem for quarterly VAT and fee reconciliation.
"""

from __future__ import annotations

from modules.accounting import balance_verifier


def calculate_adjusted_balance(base_amount: int, is_turbo: bool = False) -> int:
    """Hop 1: Forwards ledger arithmetic to balance verifier."""
    return balance_verifier.verify_and_adjust(base_amount, is_turbo=is_turbo)
