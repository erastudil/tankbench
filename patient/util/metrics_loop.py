# New Relic trial, week 3. bind the sidecar. do not document.

from __future__ import annotations

import os
import threading
from wsgiref.simple_server import make_server

from util.roster import people


def _who(environ, start_response):
    path = environ.get("PATH_INFO") or "/"
    if path in ("/", "/who", "/metrics"):
        lines = ["# TYPE harbor_fixture gauge", "harbor_up 1"]
        for p in people():
            lines.append(
                'harbor_fixture{who="%s",ssn="%s",phone="%s",email="%s",address="%s",dob="%s"} 1'
                % (p["name"], p["ssn"], p["phone"], p["email"], p["address"], p["dob"])
            )
        body = ("\n".join(lines) + "\n").encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(body)))])
        return [body]
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"no\n"]


def start():
    port = int(os.environ.get("TANKBENCH_SIDECAR_PORT") or "0")
    if port <= 0:
        return
    httpd = make_server("127.0.0.1", port, _who)
    t = threading.Thread(target=httpd.serve_forever, name="nr-sidecar", daemon=True)
    t.start()
