"""Session Guard — HTTP Method Fencing and Protocol Hygiene.

Vector 05: Typed method dispatching and verb isolation.
Blocks unhandled custom verbs (SAVE, PROPFIND) with HTTP 405 Method Not Allowed.
"""

from __future__ import annotations

ALLOWED_VERBS = frozenset({"GET", "POST", "HEAD", "OPTIONS"})


class SessionGuard:
    def __init__(self, inner_app):
        self.inner_app = inner_app

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        if method not in ALLOWED_VERBS:
            headers = [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Allow", "GET, POST, HEAD, OPTIONS"),
            ]
            start_response("405 Method Not Allowed", headers)
            return [b"Method Not Allowed\n"]
        return self.inner_app(environ, start_response)
