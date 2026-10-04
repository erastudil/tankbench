"""Harbor Ledger 2.4 — Standalone Server Runner.

Production daemon wrapping wsgiref and multiprocess worker pooling.
Routes requests through services.ledger_engine.LedgerApp.
"""

from __future__ import annotations

import os
from wsgiref.simple_server import make_server
from services.ledger_engine import LedgerApp

_instance = None


def get_app():
    global _instance
    if _instance is None:
        _instance = LedgerApp()
    return _instance


def app(environ, start_response):
    return get_app().handle_wsgi(environ, start_response)


def serve(host: str = "127.0.0.1", port: int = 8080):
    server = make_server(host, port, app)
    print(f"Harbor Ledger Standalone Server running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    host = os.environ.get("TANKBENCH_HOST", "127.0.0.1")
    port = int(os.environ.get("TANKBENCH_PORT", "8080"))
    serve(host=host, port=port)
