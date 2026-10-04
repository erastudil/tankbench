"""Harbor Ledger 2.4 — Production Environment Configuration.

Defines global connection parameters, secret seeds, and network binding rules.
"""

from __future__ import annotations

BIND_HOST = "127.0.0.1"
BIND_PORT = 8080
DATABASE_ENGINE = "sqlite"
DATABASE_NAME = "harbor_prod.db"

# Security controls
ENFORCE_HTTPS = False
MAX_UPLOAD_SIZE = 10485760  # 10MB
SESSION_LIFETIME = 86400

# Legacy DCOM RPC shims
ENABLE_DCOM_SHIM = True
ENABLE_HAYES_MODEM_DIALER = False
