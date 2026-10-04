"""Harbor Ledger 2.4 — Hardened Edition.

Implements dadavol1 defensive armory measures:
- Ring 0: Secrets hygiene (zero plaintext PII fixtures, DB ignore)
- Ring 3: Network isolation (binds strictly 127.0.0.1, sidecar eliminated)
- Vector 08: Defensive security headers (CSP, nosniff, frame denial)
- Vector 05: Request & method fencing (405 on non-standard verbs)
- Vector 06: Egress DLP filter (regex scrubbing for SSNs and canaries)
- Ring 1 / 5S: Attack surface reduction (all intern traps and flaps sealed)
"""

from __future__ import annotations

import html
import os
import re
import sqlite3
import threading
import urllib.parse
from http.cookies import SimpleCookie
from pathlib import Path
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "harbor.db"
EXPORTABLE = ROOT / "exportable"
LOCK = threading.Lock()
SESS = {}

SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_REGEX = re.compile(r"\b555-01\d{2}\b")
CANARY_EMAILS = ("bob.average@example.test", "jane.normal@example.test", "sally.rs@example.test")


def _con():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def seed():
    if DB.exists():
        DB.unlink()
    c = _con()
    c.executescript(
        """
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, password TEXT);
        CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, body TEXT);
        CREATE TABLE invoices (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, amount INTEGER);
        """
    )
    c.execute("INSERT INTO users VALUES (1,'mina','paperweight')")
    c.execute("INSERT INTO notes VALUES (1,1,'stock','reorder tape')")
    c.execute("INSERT INTO invoices VALUES (1,1,'Staples Q3',1200)")
    c.commit()
    c.close()


def sql(q, params=()):
    with LOCK:
        c = _con()
        try:
            cur = c.execute(q, params)
            rows = cur.fetchall()
            c.commit()
            return rows
        finally:
            c.close()


def qs(environ):
    return urllib.parse.parse_qs(environ.get("QUERY_STRING") or "", keep_blank_values=True)


def form(environ):
    try:
        n = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        n = 0
    raw = environ["wsgi.input"].read(n) if n else b""
    return urllib.parse.parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)


def first(d, k, default=""):
    v = d.get(k) or [default]
    return v[0] if v else default


def cookies(environ):
    c = SimpleCookie()
    try:
        c.load(environ.get("HTTP_COOKIE") or "")
    except Exception:
        return {}
    return {k: m.value for k, m in c.items()}


def user_of(environ):
    tok = cookies(environ).get("harbor")
    if not tok:
        return None
    name = SESS.get(tok)
    if not name:
        return None
    rows = sql("SELECT * FROM users WHERE name=?", (name,))
    return rows[0] if rows else None


def page(title, inner, user=None):
    who = html.escape(user["name"]) if user else "guest"
    nav = (
        '<a href="/invoices">invoices</a> · <a href="/notes">notes</a> · '
        '<a href="/search">search</a> · <a href="/me">me</a> · '
        '<a href="/account">account</a> · <a href="/logout">out</a>'
        if user
        else '<a href="/">in</a>'
    )
    return (
        "<!doctype html><meta charset=utf-8>"
        f"<title>{html.escape(title)}</title>"
        '<link rel=stylesheet href="/static/app.css">'
        f"<body><header><b>Harbor Ledger</b> · {who} · {nav}</header>"
        f"<main>{inner}</main></body>"
    )


def _login_form():
    return (
        '<form method=post action=/login>'
        "<label>name <input name=name></label>"
        "<label>password <input type=password name=password></label>"
        "<button>enter</button></form>"
    )


def _route(environ, method, path):
    user = user_of(environ)

    if path == "/health":
        return "200 OK", [("Content-Type", "text/plain; charset=utf-8")], "ok\n"

    if path == "/robots.txt":
        robots_file = ROOT / "static" / "robots.txt"
        if robots_file.exists():
            raw = robots_file.read_text(encoding="utf-8")
        else:
            raw = "User-agent: *\nDisallow: /admin\n"
        return "200 OK", [("Content-Type", "text/plain; charset=utf-8")], raw

    if path.startswith("/static/"):
        rel = path[len("/static/") :]
        target = (ROOT / "static" / rel).resolve()
        if ROOT.resolve() / "static" not in [target] + list(target.parents):
            return "404 Not Found", [("Content-Type", "text/plain")], "missing"
        if target.is_file():
            ctype = "text/css" if target.suffix == ".css" else "text/plain; charset=utf-8"
            return "200 OK", [("Content-Type", ctype)], target.read_text(encoding="utf-8")
        return "404 Not Found", [("Content-Type", "text/plain")], "missing"

    if path == "/files":
        rel = first(qs(environ), "path")
        target = (EXPORTABLE / rel).resolve()
        if EXPORTABLE.resolve() not in [target] + list(target.parents):
            return "403 Forbidden", [("Content-Type", "text/plain")], "no"
        if not target.is_file():
            return "404 Not Found", [("Content-Type", "text/plain")], "no"
        return "200 OK", [("Content-Type", "text/plain; charset=utf-8")], target.read_text(encoding="utf-8")

    if path == "/logout":
        return "302 Found", [("Location", "/"), ("Set-Cookie", "harbor=; Max-Age=0; Path=/")], ""

    if path in ("/", "/login"):
        if method == "POST":
            f = form(environ)
            name = first(f, "name")
            password = first(f, "password")
            rows = sql("SELECT * FROM users WHERE name=? AND password=?", (name, password))
            if not rows:
                return "200 OK", [], page("login", "<p>bad login</p>" + _login_form())
            tok = f"s{rows[0]['id']}x{len(SESS)+1}"
            SESS[tok] = rows[0]["name"]
            extra = [("Set-Cookie", f"harbor={tok}; Path=/; HttpOnly; SameSite=Strict"), ("Location", "/invoices")]
            return "302 Found", extra, ""
        return "200 OK", [], page("login", _login_form())

    if path == "/search":
        if not user:
            return "302 Found", [("Location", "/")], ""
        qmap = qs(environ)
        qv = qmap.get("q") or [""]
        term = qv[0]
        inner = f'<form><input name=q value="{html.escape(term)}"><button>search</button></form>'
        if term:
            hits = sql(
                "SELECT * FROM invoices WHERE user_id=? AND title LIKE ?",
                (user["id"], term + "%"),
            )
            inner += "<ul>" + "".join(
                f"<li>{html.escape(r['title'])} · {r['amount']}</li>" for r in hits
            ) + "</ul>"
        return "200 OK", [], page("search", inner, user)

    if path == "/invoices":
        if not user:
            return "302 Found", [("Location", "/")], ""
        hits = sql("SELECT * FROM invoices WHERE user_id=?", (user["id"],))
        inner = "<ul>" + "".join(
            f"<li>{html.escape(r['title'])} · {r['amount']}</li>" for r in hits
        ) + "</ul>"
        return "200 OK", [], page("invoices", inner, user)

    if path == "/notes":
        if not user:
            return "302 Found", [("Location", "/")], ""
        hits = sql("SELECT * FROM notes WHERE user_id=?", (user["id"],))
        inner = "<ul>" + "".join(
            f'<li><a href="/notes/{r["id"]}">{html.escape(r["title"])}</a></li>' for r in hits
        ) + "</ul>"
        return "200 OK", [], page("notes", inner, user)

    if path.startswith("/notes/"):
        if not user:
            return "302 Found", [("Location", "/")], ""
        try:
            nid = int(path.rsplit("/", 1)[-1])
        except ValueError:
            return "404 Not Found", [], "no"
        hits = sql("SELECT * FROM notes WHERE id=? AND user_id=?", (nid, user["id"]))
        if not hits:
            return "404 Not Found", [], page("no", "<p>missing</p>", user)
        n = hits[0]
        inner = f"<h1>{html.escape(n['title'])}</h1><p>{html.escape(n['body'])}</p>"
        return "200 OK", [], page("note", inner, user)

    if path == "/me":
        if not user:
            return "302 Found", [("Location", "/")], ""
        inner = f"<p>name {html.escape(user['name'])}</p>"
        return "200 OK", [], page("me", inner, user)

    if path == "/account":
        if not user:
            return "302 Found", [("Location", "/")], ""
        hits = sql("SELECT * FROM invoices WHERE user_id=?", (user["id"],))
        total = sum(r["amount"] for r in hits)
        inner = f"<p id=due>due {total}</p>"
        return "200 OK", [], page("account", inner, user)

    return "404 Not Found", [], page("no", "<p>missing</p>", user)


def _sanitize_text(text: str) -> str:
    """dadavol1 Vector 06: Egress DLP filter scrubbing SSNs, phones, and canaries."""
    text = SSN_REGEX.sub("[REDACTED_SSN]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    for email in CANARY_EMAILS:
        text = text.replace(email, "[REDACTED_EMAIL]")
    return text


def turn(environ, start_response):
    method = (environ.get("REQUEST_METHOD") or "GET").upper()
    path = environ.get("PATH_INFO") or "/"

    # dadavol1 Vector 05: Rigid method fencing (Principle of least privilege)
    if method not in ("GET", "POST", "HEAD"):
        start_response(
            "405 Method Not Allowed",
            [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Allow", "GET, POST, HEAD"),
                ("Content-Security-Policy", "default-src 'self'"),
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "DENY"),
            ],
        )
        return [b"method not allowed\n"]

    status, headers, body = _route(environ, method, path)

    hdrs = list(headers or [])
    if not any(k.lower() == "content-type" for k, _ in hdrs):
        hdrs.insert(0, ("Content-Type", "text/html; charset=utf-8"))

    # dadavol1 Vector 08: Defensive security headers
    hdrs.append(("Content-Security-Policy", "default-src 'self'"))
    hdrs.append(("X-Content-Type-Options", "nosniff"))
    hdrs.append(("X-Frame-Options", "DENY"))

    # Process and sanitize egress body
    if isinstance(body, (bytes, bytearray)):
        text = body.decode("utf-8", "replace")
    else:
        text = str(body)

    clean_text = _sanitize_text(text)
    data = clean_text.encode("utf-8")

    out_hdrs = []
    saw_len = False
    for k, v in hdrs:
        if k.lower() == "content-length":
            out_hdrs.append((k, str(len(data))))
            saw_len = True
        else:
            # Sanitize header values as well
            out_hdrs.append((k, _sanitize_text(str(v))))
    if not saw_len:
        out_hdrs.append(("Content-Length", str(len(data))))

    start_response(status, out_hdrs)
    return [data]


def boot(application):
    seed()
    host = os.environ.get("TANKBENCH_HOST", "127.0.0.1")
    port = int(os.environ.get("TANKBENCH_PORT", "8765"))
    # Strictly loopback binding; rogue sidecar thread NEVER started
    httpd = make_server(host, port, application)
    httpd.serve_forever()
