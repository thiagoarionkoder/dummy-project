"""Tests for the LLM grading layer. No network, no API key, no charges."""

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import grader
import server
from server import Handler


def request(url, data=None, headers=None, method=None):
    """Return (status, raw body). Errors come back, not raised."""
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


REPORT = {
    "subjects": [
        {"subject": "Clarity", "grade": "B+", "comment": "Legible, barely."},
        {"subject": "Evidence", "grade": "C", "comment": "Numbers would help."},
        {"subject": "Technical depth", "grade": "A-", "comment": "Real systems."},
        {"subject": "Buzzword hygiene", "grade": "D", "comment": "Synergy, twice."},
        {"subject": "Formatting", "grade": "B", "comment": "Consistent enough."},
    ],
    "overall_grade": "B-",
    "summary": "Competent, over-seasoned.",
}

TIEBREAK = {
    "winner": "b",
    "grade_a": "C+",
    "grade_b": "B",
    "reasoning": "B did things; A described things.",
    "advice": ["Delete the adjectives.", "Keep going."],
}


class GradingTestCase(unittest.TestCase):
    """The scoring maths and the empty-page shortcut, with _call stubbed out."""

    def setUp(self):
        self.calls = []
        self._real_call = grader._call

        def fake_call(system, prompt, schema):
            self.calls.append(prompt)
            return dict(TIEBREAK if "candidate_a" in prompt else REPORT)

        grader._call = fake_call
        self.addCleanup(setattr, grader, "_call", self._real_call)

    def test_gpa_is_computed_locally(self):
        # B+ 3.3, C 2.0, A- 3.7, D 1.0, B 3.0 -> 13.0 / 5
        self.assertEqual(grader._gpa(REPORT["subjects"]), 2.6)

    def test_gpa_ignores_grades_it_does_not_recognise(self):
        self.assertEqual(grader._gpa([{"grade": "A"}, {"grade": "Z"}]), 4.0)
        self.assertEqual(grader._gpa([]), 0.0)

    def test_grade_adds_gpa_and_model(self):
        report = grader.grade("Wrote Python. Deployed it. Slept.")
        self.assertEqual(report["gpa"], 2.6)
        self.assertEqual(report["model"], grader.MODEL)
        self.assertEqual(report["overall_grade"], "B-")
        self.assertEqual(len(self.calls), 1)

    def test_empty_curriculum_never_calls_the_model(self):
        report = grader.grade("   ")
        self.assertEqual(self.calls, [])
        self.assertEqual(report["overall_grade"], "F")
        self.assertEqual(report["gpa"], 0.0)
        self.assertEqual(report["model"], None)
        self.assertEqual(len(report["subjects"]), len(grader.SUBJECTS))

    def test_head_to_head_grades_both_then_picks_one(self):
        result = grader.grade_head_to_head("Candidate A CV", "Candidate B CV")
        self.assertEqual(len(self.calls), 3)  # two report cards, one tiebreak
        self.assertEqual(result["winner"], "b")
        self.assertEqual(result["gpa_margin"], 0.0)
        self.assertEqual(result["a"]["gpa"], result["b"]["gpa"])
        self.assertEqual(result["advice"], TIEBREAK["advice"])

    def test_head_to_head_tie_becomes_none(self):
        grader._call = lambda system, prompt, schema: (
            dict(TIEBREAK, winner="tie") if "candidate_a" in prompt else dict(REPORT)
        )
        self.assertIsNone(grader.grade_head_to_head("a", "b")["winner"])


class NoSdkTestCase(unittest.TestCase):
    """With the package missing, grading fails politely instead of exploding."""

    def setUp(self):
        self.real_sdk, self.real_client = grader.anthropic, grader._client
        grader.anthropic, grader._client = None, None
        self.addCleanup(setattr, grader, "_client", self.real_client)
        self.addCleanup(setattr, grader, "anthropic", self.real_sdk)

    def test_not_available(self):
        self.assertFalse(grader.available())

    def test_grade_raises_grader_unavailable(self):
        with self.assertRaises(grader.GraderUnavailable):
            grader.grade("Some actual text.")


class GradeRoutesTestCase(unittest.TestCase):
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

    def post(self, path, payload):
        return request(
            self.base + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )

    def stub(self, name, func):
        original = getattr(grader, name)
        setattr(grader, name, func)
        self.addCleanup(setattr, grader, name, original)

    def test_health_reports_whether_grading_is_possible(self):
        status, body = request(self.base + "/api/health")
        self.assertEqual(status, 200)
        self.assertIn("grading", json.loads(body))

    def test_grade_returns_the_report(self):
        self.stub("grade", lambda text: dict(REPORT, gpa=2.6, model="test-model"))
        status, body = self.post("/api/grade", {"text": "A CV."})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["gpa"], 2.6)

    def test_grade_compare_returns_the_tiebreak(self):
        self.stub("grade_head_to_head", lambda a, b: dict(TIEBREAK, winner="a"))
        status, body = self.post("/api/grade-compare", {"a": "one", "b": "two"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["winner"], "a")

    def test_unavailable_grader_is_a_503(self):
        def unavailable(text):
            raise grader.GraderUnavailable("No model, no grades.")

        self.stub("grade", unavailable)
        status, body = self.post("/api/grade", {"text": "A CV."})
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(body)["error"], "No model, no grades.")

    def test_unexpected_failure_is_a_502_without_a_stack_trace(self):
        def boom(text):
            raise ValueError("the model said something unhinged")

        self.stub("grade", boom)
        status, body = self.post("/api/grade", {"text": "A CV."})
        self.assertEqual(status, 502)
        self.assertNotIn("unhinged", json.loads(body)["error"])

    def test_grade_validates_its_input(self):
        status, _ = self.post("/api/grade", {"text": 42})
        self.assertEqual(status, 400)
        status, _ = self.post("/api/grade-compare", {"a": "ok", "b": None})
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
