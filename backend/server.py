"""Curriculum Analyser backend. Stdlib only, because life is short."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

import deployment
from analyser import analyse, compare

PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "0.0.0.0")
FRONTEND = os.path.realpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
)

MAX_BODY = 200_000

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".png": "image/png",
}


def resolve_static(path: str):
    """Map a URL path to a file inside FRONTEND, or None if it escapes."""
    rel = unquote(path).lstrip("/") or "index.html"
    if "\x00" in rel:
        return None
    target = os.path.realpath(os.path.join(FRONTEND, rel))
    if target != FRONTEND and not target.startswith(FRONTEND + os.sep):
        return None
    return target if os.path.isfile(target) else None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, status, body, content_type="application/json", headers=()):
        payload = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        for name, value in deployment.headers():
            self.send_header(name, value)
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _error(self, status, message):
        self._send(status, json.dumps({"error": message}))

    def _abort(self, status, message):
        """Reject a request whose body we never read; keep-alive can't continue."""
        self.close_connection = True
        self._error(status, message)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/health":
            return self._send(200, json.dumps(
                {"ok": True, "mood": "judgemental", **deployment.info()}))

        if path == "/api/region":
            return self._send(200, json.dumps(deployment.info()))

        target = resolve_static(path)
        if target is None:
            return self._error(404, "not found")

        try:
            with open(target, "rb") as fh:
                body = fh.read()
        except OSError:
            return self._error(404, "not found")

        ext = os.path.splitext(target)[1]
        self._send(200, body, CONTENT_TYPES.get(ext, "application/octet-stream"),
                   headers=[("Cache-Control", "no-cache")])

    do_HEAD = do_GET

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in ("/api/analyse", "/api/compare"):
            return self._abort(404, "not found")

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._abort(400, "invalid Content-Length")
        if length < 0:
            return self._abort(400, "invalid Content-Length")
        if length > MAX_BODY:
            return self._abort(413, "That is a novel, not a CV.")

        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._error(400, "invalid JSON")

        if not isinstance(data, dict):
            return self._error(400, "body must be a JSON object")

        if path == "/api/compare":
            texts = []
            for key in ("a", "b"):
                value = data.get(key, "")
                if not isinstance(value, str):
                    return self._error(400, f"'{key}' must be a string")
                texts.append(value)
            return self._send(200, json.dumps(compare(*texts)))

        text = data.get("text", "")
        if not isinstance(text, str):
            return self._error(400, "'text' must be a string")

        self._send(200, json.dumps(analyse(text)))

    def log_message(self, *args):
        pass  # shhh


if __name__ == "__main__":
    print(f"Curriculum Analyser judging candidates at http://localhost:{PORT}")
    print(f"Region: {deployment.REGION} ({deployment.CITY}, {deployment.COUNTRY}) "
          f"| {deployment.TIMEZONE} | data stays in {deployment.DATA_RESIDENCY}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
