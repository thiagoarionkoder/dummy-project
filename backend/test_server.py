"""Tests for the HTTP layer: routing, limits, and not serving the whole disk."""

import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import deployment
import server
from server import Handler, resolve_static


def request(url, data=None, headers=None, method=None):
    """Return (status, parsed_or_raw_body). Errors come back, not raised."""
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, res.read(), res.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers


class ServerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)

    def post(self, body, headers=None):
        status, raw, _ = request(
            self.base + "/api/analyse",
            data=body if isinstance(body, bytes) else json.dumps(body).encode(),
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            return status, json.loads(raw)
        except json.JSONDecodeError:
            return status, raw


class TestRouting(ServerTestCase):
    def test_health(self):
        status, raw, _ = request(self.base + "/api/health")
        self.assertEqual(status, 200)
        body = json.loads(raw)
        self.assertTrue(body["ok"])
        self.assertEqual(body["region"], deployment.REGION)

    def test_index_is_served_at_root(self):
        status, raw, headers = request(self.base + "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Curriculum Analyser", raw)
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")

    def test_assets_have_correct_content_type(self):
        for path, ctype in [("/style.css", "text/css; charset=utf-8"),
                            ("/app.js", "text/javascript; charset=utf-8")]:
            with self.subTest(path=path):
                status, _, headers = request(self.base + path)
                self.assertEqual(status, 200)
                self.assertEqual(headers["Content-Type"], ctype)

    def test_unknown_paths_are_404(self):
        for path in ("/nope", "/api/nope", "/frontend"):
            with self.subTest(path=path):
                self.assertEqual(request(self.base + path)[0], 404)

    def test_post_to_wrong_path_is_404(self):
        status, _, _ = request(self.base + "/api/nope", data=b"{}", method="POST")
        self.assertEqual(status, 404)

    def test_query_string_is_ignored(self):
        self.assertEqual(request(self.base + "/api/health?cache=bust")[0], 200)

    def test_head_returns_headers_without_body(self):
        status, raw, headers = request(self.base + "/", method="HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(raw, b"")
        self.assertNotEqual(headers["Content-Length"], "0")


class TestDeploymentRegion(ServerTestCase):
    """The deployment claims to be in Europe; make it say so consistently."""

    def test_region_endpoint_reports_an_eu_region(self):
        status, raw, _ = request(self.base + "/api/region")
        self.assertEqual(status, 200)
        body = json.loads(raw)
        self.assertTrue(body["region"].startswith("eu-"))
        self.assertTrue(body["timezone"].startswith("Europe/"))
        self.assertEqual(body["data_residency"], "EU")
        self.assertTrue(body["gdpr"])

    def test_region_headers_are_on_every_response(self):
        for path in ("/", "/api/health", "/style.css", "/nope"):
            with self.subTest(path=path):
                _, _, headers = request(self.base + path)
                self.assertEqual(headers["X-Deployment-Region"], deployment.REGION)
                self.assertEqual(headers["X-Data-Residency"], "EU")
                self.assertEqual(headers["X-Deployment-Timezone"], deployment.TIMEZONE)

    def test_every_configured_region_is_european(self):
        for name, meta in deployment.REGIONS.items():
            with self.subTest(region=name):
                self.assertTrue(name.startswith("eu-"))
                self.assertTrue(meta["timezone"].startswith("Europe/"))


class TestStaticContainment(unittest.TestCase):
    """resolve_static must never hand out a file outside the frontend dir."""

    def test_serves_real_frontend_files(self):
        for path in ("/", "/index.html", "/style.css", "/app.js"):
            with self.subTest(path=path):
                self.assertIsNotNone(resolve_static(path))

    def test_rejects_parent_traversal(self):
        for path in ("/../backend/server.py", "/../../etc/passwd",
                     "/%2e%2e/backend/analyser.py", "/....//backend/server.py"):
            with self.subTest(path=path):
                self.assertIsNone(resolve_static(path))

    def test_rejects_sibling_directory_with_shared_prefix(self):
        """A `startswith` check would leak `frontend-secrets/`; this must not."""
        sibling = server.FRONTEND + "-secrets"
        os.makedirs(sibling, exist_ok=True)
        self.addCleanup(shutil.rmtree, sibling, ignore_errors=True)
        with open(os.path.join(sibling, "keys.txt"), "w") as fh:
            fh.write("hunter2")
        self.assertIsNone(resolve_static("/../frontend-secrets/keys.txt"))

    def test_rejects_absolute_and_null_bytes(self):
        self.assertIsNone(resolve_static("/etc/passwd"))
        self.assertIsNone(resolve_static("/index.html\x00.css"))

    def test_directories_are_not_files(self):
        with tempfile.TemporaryDirectory(dir=server.FRONTEND) as d:
            self.assertIsNone(resolve_static("/" + os.path.basename(d)))


class TestAnalyseEndpoint(ServerTestCase):
    def test_happy_path(self):
        status, body = self.post({"text": "Python, Docker, SQL. 5 years."})
        self.assertEqual(status, 200)
        self.assertIn("score", body)
        self.assertIn("python", body["found_skills"])

    def test_missing_text_is_treated_as_empty(self):
        status, body = self.post({})
        self.assertEqual(status, 200)
        self.assertEqual(body["verdict"], "EMPTY")

    def test_malformed_json_is_400_not_500(self):
        status, body = self.post(b"{not json")
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    def test_non_object_body_is_400_not_500(self):
        for raw in (b'"just a string"', b"[1, 2, 3]", b"42", b"null"):
            with self.subTest(raw=raw):
                self.assertEqual(self.post(raw)[0], 400)

    def test_non_string_text_is_400_not_500(self):
        for value in (123, ["a"], {"a": 1}, True):
            with self.subTest(value=value):
                self.assertEqual(self.post({"text": value})[0], 400)

    def test_oversized_body_is_rejected(self):
        status, body = self.post({"text": "x" * (server.MAX_BODY + 1)})
        self.assertEqual(status, 413)
        self.assertIn("novel", body["error"])

    def test_body_just_under_the_limit_is_accepted(self):
        text = "python " * 1000
        payload = json.dumps({"text": text}).encode()
        self.assertLess(len(payload), server.MAX_BODY)
        self.assertEqual(self.post({"text": text})[0], 200)

    def test_unicode_survives_the_round_trip(self):
        status, body = self.post({"text": "Résumé: Python, 日本語 🚀, 3 years"})
        self.assertEqual(status, 200)
        self.assertIn("python", body["found_skills"])


if __name__ == "__main__":
    unittest.main()
