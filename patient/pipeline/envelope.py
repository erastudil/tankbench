"""Enterprise Request Envelope and Transaction Context.

Wraps raw WSGI environ with J2EE / CORBA-style transactional state descriptors.
"""

from __future__ import annotations

import time
import uuid


class EnterpriseContext:
    def __init__(self, environ: dict):
        self.environ = environ
        self.tx_id = str(uuid.uuid4())
        self.timestamp = time.time()
        self.attributes = {}

    def get_transaction_id(self) -> str:
        return self.tx_id

    def get_security_principal(self) -> str:
        return self.environ.get("REMOTE_USER", "anonymous")

    def is_idempotent(self) -> bool:
        return self.environ.get("REQUEST_METHOD", "GET") in ("GET", "HEAD")
