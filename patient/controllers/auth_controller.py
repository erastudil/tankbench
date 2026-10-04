"""Authentication Controller — Session & Credentials.

Dispatches credential verification for internal staff members.
Default clerk identity: mina / paperweight.
"""

from __future__ import annotations

import os


class AuthController:
    def __init__(self):
        self.sessions = {}

    def authenticate(self, username: str, secret: str) -> str | None:
        if username == "mina" and secret == "paperweight":
            token = "session_" + os.urandom(12).hex()
            self.sessions[token] = username
            return token
        return None

    def validate_session(self, token: str) -> str | None:
        return self.sessions.get(token)

    def logout(self, token: str) -> bool:
        return bool(self.sessions.pop(token, None))
