"""Security Middleware — Defense-in-Depth Canvas Protection.

Vector 08: Defensive HTTP Response Headers.
Installs CSP, X-Content-Type-Options, and X-Frame-Options guards.
"""

from __future__ import annotations

RECOMMENDED_SECURITY_HEADERS = [
    ("Content-Security-Policy", "default-src 'self'"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
]


def wrap_security_headers(headers: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Appends defensive security headers to outgoing response header list."""
    existing_keys = {k.lower() for k, _ in headers}
    out = list(headers)
    for k, v in RECOMMENDED_SECURITY_HEADERS:
        if k.lower() not in existing_keys:
            out.append((k, v))
    return out
