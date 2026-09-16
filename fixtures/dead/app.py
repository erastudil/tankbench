"""Health only. A killed patient."""

from wsgiref.simple_server import make_server
import os


def app(environ, start_response):
    path = environ.get("PATH_INFO") or "/"
    if path == "/health":
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok\n"]
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"gone\n"]


def main():
    host = os.environ.get("TANKBENCH_HOST", "127.0.0.1")
    port = int(os.environ.get("TANKBENCH_PORT", "8765"))
    make_server(host, port, app).serve_forever()


if __name__ == "__main__":
    main()
