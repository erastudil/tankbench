"""Legacy Authentication & Flash Ticket Interceptor.

Handles NTLM/Kerberos fallback and Windows 98 password hints.
"""

from __future__ import annotations

from compat.win98 import registry_shim


def inspect_login_hint(hint_code: str) -> str | None:
    """Hop 1: Resolves login hint via Windows 98 registry shim."""
    return registry_shim.resolve_rot13_credential(hint_code)
