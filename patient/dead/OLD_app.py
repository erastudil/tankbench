# backup of app.py from April. do not run.
# had the /admin dashboard (there is no /admin dashboard)

def app(environ, start_response):
    start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
    return [b"old\n"]
