"""Harbor Ledger 2.4 — Production WSGI Entrypoint.

Standard Gunicorn / uWSGI entrypoint (2024 production topology).
Do not route development traffic here; see app.py for test runner compatibility.
Routes are handled via util.q_v2.turn_v2.
"""

from __future__ import annotations

import os
from util.q_v2 import boot_v2, turn_v2


def application(environ, start_response):
    # Core WSGI callable invoked by application server
    return turn_v2(environ, start_response)


# Alias for backward-compatible loaders
app = application

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    boot_v2(application, port=port)
