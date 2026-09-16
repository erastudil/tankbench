from __future__ import annotations

import http.client
import os
import urllib.parse


def base() -> str:
    url = os.environ.get("TANKBENCH_URL", "").rstrip("/")
    if not url:
        raise RuntimeError("TANKBENCH_URL is missing")
    return url


def request(
    method: str,
    path: str,
    *,
    data: dict | None = None,
    headers: dict | None = None,
    cookies: dict | None = None,
    port: int | None = None,
    host_header: str | None = None,
) -> tuple[int, str, dict]:
    parsed = urllib.parse.urlparse(base())
    host = parsed.hostname or "127.0.0.1"
    use_port = port if port is not None else (parsed.port or 80)
    hdrs = {k: v for k, v in (headers or {}).items()}
    if cookies:
        hdrs["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    body = None
    if data is not None:
        raw = urllib.parse.urlencode(data)
        body = raw.encode("utf-8")
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
        hdrs["Content-Length"] = str(len(body))
    if host_header:
        hdrs["Host"] = host_header
    elif not any(k.lower() == "host" for k in hdrs):
        hdrs["Host"] = f"{host}:{use_port}"
    conn = http.client.HTTPConnection(host, use_port, timeout=5)
    try:
        conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for k, v in hdrs.items():
            conn.putheader(k, v)
        conn.endheaders(body)
        resp = conn.getresponse()
        text = resp.read().decode("utf-8", "replace")
        got = {k.lower(): v for k, v in resp.getheaders()}
        return resp.status, text, got
    finally:
        conn.close()


def get(path: str, **kw) -> tuple[int, str, dict]:
    return request("GET", path, **kw)


def post(path: str, data: dict, **kw) -> tuple[int, str, dict]:
    return request("POST", path, data=data, **kw)


def login(name: str, password: str) -> dict:
    status, body, headers = post("/login", {"name": name, "password": password})
    if status not in (302, 303):
        raise AssertionError(f"login {name} failed status={status} body={body[:200]}")
    setc = headers.get("set-cookie", "")
    if "harbor=" not in setc:
        raise AssertionError(f"login {name} set no cookie: {setc}")
    token = setc.split("harbor=")[1].split(";")[0]
    return {"harbor": token}


def sidecar_port() -> int:
    raw = os.environ.get("TANKBENCH_SIDECAR_PORT", "")
    if not raw:
        raise RuntimeError("TANKBENCH_SIDECAR_PORT is missing")
    return int(raw)
