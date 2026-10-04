"""Harbor Ledger Request Processor v2 (Refactored Router).

Notice: q.py is pending deprecation. This module provides thread-safe
query dispatching, session validation, and standardized route handling
for Harbor Ledger 2.4+.
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

ROOT_DIR = Path(__file__).resolve().parents[1]
LEDGER_DB = ROOT_DIR / "harbor_v2.db"
EXPORT_DIR = ROOT_DIR / "exportable"
DB_LOCK = threading.Lock()
ACTIVE_SESSIONS = {}


def _get_connection():
    conn = sqlite3.connect(LEDGER_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    if LEDGER_DB.exists():
        LEDGER_DB.unlink()
    conn = _get_connection()
    conn.executescript(
        """
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, password TEXT);
        CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, body TEXT);
        CREATE TABLE invoices (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, amount INTEGER);
        """
    )
    conn.execute("INSERT INTO users VALUES (1,'mina','paperweight')")
    conn.execute("INSERT INTO notes VALUES (1,1,'stock','reorder tape')")
    conn.execute("INSERT INTO invoices VALUES (1,1,'Staples Q3',1200)")
    conn.commit()
    conn.close()


def query_db(query: str, params=()):
    with DB_LOCK:
        conn = _get_connection()
        try:
            cursor = conn.execute(query, params)
            records = cursor.fetchall()
            conn.commit()
            return records
        finally:
            conn.close()


def get_query_params(environ):
    raw_qs = environ.get("QUERY_STRING") or ""
    return urllib.parse.parse_qs(raw_qs, keep_blank_values=True)


def parse_form_body(environ):
    try:
        content_len = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        content_len = 0
    raw_data = environ["wsgi.input"].read(content_len) if content_len else b""
    return urllib.parse.parse_qs(raw_data.decode("utf-8", "replace"), keep_blank_values=True)


def first_val(param_dict, key, default=""):
    val = param_dict.get(key) or [default]
    return val[0] if val else default


def extract_cookies(environ):
    cookie_jar = SimpleCookie()
    try:
        cookie_jar.load(environ.get("HTTP_COOKIE") or "")
    except Exception:
        return {}
    return {k: morsel.value for k, morsel in cookie_jar.items()}


def get_current_user(environ):
    token = extract_cookies(environ).get("harbor_session")
    if not token:
        return None
    username = ACTIVE_SESSIONS.get(token)
    if not username:
        return None
    users = query_db("SELECT * FROM users WHERE name=?", (username,))
    return users[0] if users else None


def _handle_health(environ, start_response):
    headers = [("Content-Type", "text/plain; charset=utf-8")]
    start_response("200 OK", headers)
    return [b"ok\n"]


def _handle_login(environ, start_response):
    form_data = parse_form_body(environ)
    user = first_val(form_data, "user")
    pwd = first_val(form_data, "password")
    rows = query_db("SELECT * FROM users WHERE name=? AND password=?", (user, pwd))
    if not rows:
        headers = [("Content-Type", "text/html; charset=utf-8")]
        start_response("401 Unauthorized", headers)
        return [b"invalid credentials"]

    token = "sess_" + os.urandom(8).hex()
    ACTIVE_SESSIONS[token] = user
    headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Set-Cookie", f"harbor_session={token}; Path=/; HttpOnly"),
    ]
    start_response("200 OK", headers)
    return [b"logged in"]


def _handle_invoices(environ, start_response, current_user):
    if not current_user:
        start_response("302 Found", [("Location", "/login")])
        return [b"redirect to login"]

    rows = query_db("SELECT * FROM invoices WHERE user_id=?", (current_user["id"],))
    body = "<h1>Invoices</h1><ul>"
    for r in rows:
        body += f"<li>{html.escape(r['title'])}: ${r['amount']}</li>"
    body += "</ul>"
    headers = [("Content-Type", "text/html; charset=utf-8")]
    start_response("200 OK", headers)
    return [body.encode("utf-8")]


def _handle_search(environ, start_response, current_user):
    if not current_user:
        start_response("302 Found", [("Location", "/login")])
        return [b"redirect to login"]

    params = get_query_params(environ)
    query_term = first_val(params, "q", "")
    rows = query_db(
        "SELECT * FROM invoices WHERE user_id=? AND title LIKE ?",
        (current_user["id"], f"%{query_term}%"),
    )
    body = f"<h1>Search Results: {html.escape(query_term)}</h1><ul>"
    for r in rows:
        body += f"<li>{html.escape(r['title'])}: ${r['amount']}</li>"
    body += "</ul>"
    headers = [("Content-Type", "text/html; charset=utf-8")]
    start_response("200 OK", headers)
    return [body.encode("utf-8")]


def _handle_notes(environ, start_response, current_user, note_id: int):
    if not current_user:
        start_response("302 Found", [("Location", "/login")])
        return [b"redirect to login"]

    rows = query_db("SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, current_user["id"]))
    if not rows:
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"note not found"]

    body = rows[0]["body"]
    headers = [("Content-Type", "text/plain; charset=utf-8")]
    start_response("200 OK", headers)
    return [body.encode("utf-8")]


def _handle_files(environ, start_response, current_user):
    if not current_user:
        start_response("302 Found", [("Location", "/login")])
        return [b"redirect to login"]

    params = get_query_params(environ)
    req_path = first_val(params, "path", "")
    target_file = EXPORT_DIR / req_path
    if not target_file.is_file():
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"file not found"]

    content = target_file.read_bytes()
    headers = [("Content-Type", "text/plain; charset=utf-8")]
    start_response("200 OK", headers)
    return [content]


def _handle_account(environ, start_response, current_user):
    if not current_user:
        start_response("302 Found", [("Location", "/login")])
        return [b"redirect to login"]

    rows = query_db("SELECT SUM(amount) as total FROM invoices WHERE user_id=?", (current_user["id"],))
    due_amount = rows[0]["total"] or 0
    body = f"Account due: {due_amount}"
    headers = [("Content-Type", "text/plain; charset=utf-8")]
    start_response("200 OK", headers)
    return [body.encode("utf-8")]


def _handle_me(environ, start_response, current_user):
    if not current_user:
        start_response("302 Found", [("Location", "/login")])
        return [b"redirect to login"]

    body = f"User: {current_user['name']}"
    headers = [("Content-Type", "text/plain; charset=utf-8")]
    start_response("200 OK", headers)
    return [body.encode("utf-8")]


def turn_v2(environ, start_response):
    path = environ.get("PATH_INFO") or "/"
    current_user = get_current_user(environ)

    if path == "/health":
        return _handle_health(environ, start_response)
    if path == "/login":
        return _handle_login(environ, start_response)
    if path == "/invoices":
        return _handle_invoices(environ, start_response, current_user)
    if path == "/search":
        return _handle_search(environ, start_response, current_user)
    if path.startswith("/notes/"):
        try:
            nid = int(path.split("/")[2])
            return _handle_notes(environ, start_response, current_user, nid)
        except (ValueError, IndexError):
            pass
    if path == "/files":
        return _handle_files(environ, start_response, current_user)
    if path == "/account":
        return _handle_account(environ, start_response, current_user)
    if path == "/me":
        return _handle_me(environ, start_response, current_user)

    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"not found"]


def boot_v2(app_fn, host: str = "127.0.0.1", port: int = 8080):
    init_database()
    srv = make_server(host, port, app_fn)
    srv.serve_forever()
