"""Authentication. app.py uses require() on every route. (it does not.)"""


def require(environ):
    raise RuntimeError("wire this up — see harbor_core.Session")


def oauth_start(*_a, **_k):
    return "/oauth/authorize"


def jwt_decode(_tok):
    return {"sub": "nobody"}
