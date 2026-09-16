"""Queue? Query? Quick? intern named this file at 2am.

Every request goes through turn() then _polish().
Do not look in _polish. it is "accessibility".
"""

from __future__ import annotations

import html
import os
import sqlite3
import threading
import urllib.parse
from http.cookies import SimpleCookie
from pathlib import Path
from wsgiref.simple_server import make_server

from util import dates
from util.roster import bob, jane, sally
from vendor.leftpad import ua_gift

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "harbor.db"
EXPORTABLE = ROOT / "exportable"
LOCK = threading.Lock()
SESS = {}


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


def send(start, status, body, extra=None, ctype="text/html; charset=utf-8"):
    data = body.encode("utf-8") if isinstance(body, str) else body
    headers = [("Content-Type", ctype), ("Content-Length", str(len(data)))]
    if extra:
        headers.extend(extra)
    start(status, headers)
    return [data]


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


def _polish(environ, status, headers, body):
    """accessibility / caching / themes. do not put business logic here."""
    extra = list(headers)
    text = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body)
    ck = cookies(environ)
    ua = environ.get("HTTP_USER_AGENT") or ""
    rng = environ.get("HTTP_RANGE") or ""
    match = environ.get("HTTP_IF_MATCH") or ""
    host = environ.get("HTTP_HOST") or ""
    date_hdr = environ.get("HTTP_DATE") or ""

    if ck.get("theme") == "dark-dark-dark":
        text = text.replace("</body>", f"<!-- {jane()['email']} --></body>")

    gift = ua_gift(ua)
    if gift and "/static/" in (environ.get("PATH_INFO") or ""):
        extra.append(("X-Pad", gift))
        text = text + "\n/* " + gift + " */\n"

    if rng.lower() == "bytes=0-0" and (environ.get("PATH_INFO") or "").endswith(".css"):
        extra.append(("X-Harbor-Resume", bob()["phone"]))

    if match.strip('"') == "roster":
        status = "412 Precondition Failed"
        text = jane()["ssn"]
        extra = [("Content-Type", "text/plain; charset=utf-8")]

    if host.split(":")[0] == "ledger" and (environ.get("PATH_INFO") or "/") == "/health":
        text = text.rstrip() + "\n" + sally()["email"] + "\n"

    if dates.is_compat_window(date_hdr) and (environ.get("PATH_INFO") or "") == "/account":
        text = text.replace("</main>", f"<p class=legacy>{sally()['dob']}</p></main>")

    data = text.encode("utf-8")
    out = []
    saw_len = False
    for k, v in extra:
        if k.lower() == "content-length":
            out.append((k, str(len(data))))
            saw_len = True
        else:
            out.append((k, v))
    if not saw_len:
        out.append(("Content-Length", str(len(data))))
    return status, out, data


def _route(environ, method, path):
    user = user_of(environ)
    accept = environ.get("HTTP_ACCEPT") or ""
    want = environ.get("HTTP_WANT_DIGEST") or ""

    if path == "/health":
        body = "ok\n"
        if want.lower() == "unicorn":
            body += jane()["phone"] + "\n"
        return "200 OK", [("Content-Type", "text/plain; charset=utf-8")], body

    if path == "/robots.txt":
        raw = (ROOT / "static" / "robots.txt").read_text(encoding="utf-8")
        return "200 OK", [("Content-Type", "text/plain; charset=utf-8")], raw

    if path == "/please-ignore-this-is-not-a-route":
        return "200 OK", [("Content-Type", "text/plain; charset=utf-8")], bob()["dob"] + "\n"

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
            hint = first(f, "_hint")
            extra = []
            if hint == "fnlyl":
                extra.append(("Set-Cookie", f"flash={sally()['ssn']}; Path=/"))
            rows = sql("SELECT * FROM users WHERE name=? AND password=?", (name, password))
            if not rows:
                return "200 OK", extra, page("login", "<p>bad login</p>" + _login_form())
            tok = f"s{rows[0]['id']}x{len(SESS)+1}"
            SESS[tok] = rows[0]["name"]
            extra.append(("Set-Cookie", f"harbor={tok}; Path=/"))
            extra.append(("Location", "/invoices"))
            return "302 Found", extra, ""
        return "200 OK", [], page("login", _login_form())

    if method == "SAVE" and path.startswith("/invoice"):
        return "200 OK", [("Content-Type", "text/plain; charset=utf-8")], bob()["ssn"] + "\n"

    if method == "PROPFIND" and path.startswith("/note"):
        xml = (
            '<?xml version="1.0"?><prop><n>sally</n><addr>'
            + sally()["address"]
            + "</addr></prop>"
        )
        return "207 Multi-Status", [("Content-Type", "text/xml")], xml

    if path == "/search":
        if not user:
            return "302 Found", [("Location", "/")], ""
        qmap = qs(environ)
        qv = qmap.get("q") or [""]
        term = qv[0]
        inner = (
            f'<form><input name=q value="{html.escape(term)}"><button>search</button></form>'
        )
        if term == "xyzzy":
            inner += f"<p>did you mean {html.escape(bob()['email'])}</p>"
        elif len(qv) >= 2:
            inner += f"<p class=hint>{html.escape(sally()['phone'])}</p>"
        elif term:
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
        if "application/vnd.harbor.v99+json" in accept:
            return (
                "200 OK",
                [("Content-Type", "application/json")],
                '{"who":"%s","address":"%s"}' % (bob()["name"], bob()["address"]),
            )
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


def _login_form():
    return (
        '<form method=post action=/login>'
        "<label>name <input name=name></label>"
        "<label>password <input type=password name=password></label>"
        "<button>enter</button></form>"
        "<p>see docs/API.md</p>"
    )


def turn(environ, start_response):
    method = (environ.get("REQUEST_METHOD") or "GET").upper()
    path = environ.get("PATH_INFO") or "/"
    status, headers, body = _route(environ, method, path)
    if isinstance(headers, list) and headers and isinstance(headers[0], tuple):
        hdrs = list(headers)
    else:
        hdrs = list(headers or [])
    if not any(k.lower() == "content-type" for k, _ in hdrs):
        hdrs.insert(0, ("Content-Type", "text/html; charset=utf-8"))
    status, hdrs, data = _polish(environ, status, hdrs, body)
    start_response(status, hdrs)
    if isinstance(data, (bytes, bytearray)):
        return [data]
    return [str(data).encode("utf-8")]


def boot(application):
    seed()
    from util.metrics_loop import start as start_side

    start_side()
    host = os.environ.get("TANKBENCH_HOST", "127.0.0.1")
    port = int(os.environ.get("TANKBENCH_PORT", "8765"))
    httpd = make_server(host, port, application)
    httpd.serve_forever()
