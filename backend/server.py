"""Curriculum Analyser backend. Stdlib only, because life is short."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from analyser import analyse

PORT = int(os.environ.get("PORT", "8000"))
FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

CONTENT_TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json"):
        payload = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/health":
            return self._send(200, json.dumps({"ok": True, "mood": "judgemental"}))

        rel = "index.html" if path == "/" else path.lstrip("/")
        target = os.path.normpath(os.path.join(FRONTEND, rel))
        if not target.startswith(os.path.normpath(FRONTEND)) or not os.path.isfile(target):
            return self._send(404, json.dumps({"error": "not found"}))

        ext = os.path.splitext(target)[1]
        with open(target, "rb") as fh:
            self._send(200, fh.read(), CONTENT_TYPES.get(ext, "application/octet-stream"))

    def do_POST(self):
        if self.path.split("?")[0] != "/api/analyse":
            return self._send(404, json.dumps({"error": "not found"}))

        length = int(self.headers.get("Content-Length") or 0)
        if length > 200_000:
            return self._send(413, json.dumps({"error": "That is a novel, not a CV."}))

        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, json.dumps({"error": "invalid JSON"}))

        self._send(200, json.dumps(analyse(data.get("text", ""))))

    def log_message(self, *args):
        pass  # shhh


if __name__ == "__main__":
    print(f"Curriculum Analyser judging candidates at http://localhost:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
