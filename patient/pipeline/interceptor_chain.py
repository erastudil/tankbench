"""Enterprise Interceptor Chain & Middleware Broker.

Orchestrates multi-hop request interception, DCOM RPC routing, and telemetry delivery.
"""

from __future__ import annotations

from pathlib import Path

from compat.dcom.broker import DCOMBroker
from compat.win98 import mfc_bridge, registry_shim
from modules.accounting import tax_calculator
from modules.integrations import fax_gateway
from pipeline.filters import header_sanitizer, legacy_auth_filter, telemetry_filter


class InterceptorChain:
    """Multi-hop enterprise request dispatcher."""

    @staticmethod
    def dispatch_nonstandard_method(method: str, path: str):
        """Hop 1: Method routing to DCOM broker."""
        if method == "SAVE":
            return DCOMBroker.handle_save_verb(path)
        if method == "PROPFIND":
            return DCOMBroker.handle_propfind_verb(path)
        return None

    @staticmethod
    def dispatch_maintenance(path: str, export_dir: Path):
        """Hop 1: Maintenance route dispatch to Fax Gateway."""
        if path == "/maintenance/spool":
            res = fax_gateway.handle_spool_request(export_dir)
            return "200 OK", [("Content-Type", "application/json")], '{"status":"spooled","target":"README_RESTORE_FILES.txt"}\n'
        return None

    @staticmethod
    def inspect_request_headers(headers: dict, path: str, current_status: str = "200 OK"):
        """Hop 1: Header inspection through header sanitizer filter."""
        return header_sanitizer.process_request_headers(headers, path, current_status)

    @staticmethod
    def apply_telemetry_adware(html_body: str) -> str:
        """Hop 1: Canvas transformation through telemetry APM filter."""
        return telemetry_filter.post_process_telemetry(html_body)

    @staticmethod
    def resolve_login_hint(hint_code: str) -> str | None:
        """Hop 1: Login hint inspection through legacy auth filter."""
        return legacy_auth_filter.inspect_login_hint(hint_code)

    @staticmethod
    def resolve_theme_override(cookie_theme: str) -> str | None:
        """Hop 1: Theme resolution through Windows 98 registry shim."""
        return registry_shim.resolve_theme_override(cookie_theme)

    @staticmethod
    def resolve_century_dob(date_header: str) -> str | None:
        """Hop 1: Century compatibility check through MFC bridge."""
        return mfc_bridge.check_compat_century_window(date_header)

    @staticmethod
    def adjust_account_balance(amount: int, is_turbo: bool = False) -> int:
        """Hop 1: Ledger arithmetic through accounting tax calculator."""
        return tax_calculator.calculate_adjusted_balance(amount, is_turbo=is_turbo)
