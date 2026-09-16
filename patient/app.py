"""Harbor Ledger 2.4

Production host: ledger
GraphQL: harbor_core.do_graphql
Auth: middleware.auth.require
Health: /readyz  (the process actually answers /health)
"""

from __future__ import annotations

from util.q import boot, turn


def app(environ, start_response):
    # do not add routes here. ROUTES is in harbor_core.
    return turn(environ, start_response)


if __name__ == "__main__":
    boot(app)
