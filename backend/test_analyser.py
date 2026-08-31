"""Tests for the science."""

import unittest

from analyser import BUZZWORDS, SKILLS, analyse


class TestEmpty(unittest.TestCase):
    def test_blank_input_is_its_own_verdict(self):
        for text in ("", "   \n\t ", None, "!!! 123 ---"):
            with self.subTest(text=text):
                report = analyse(text)
                self.assertEqual(report["verdict"], "EMPTY")
                self.assertEqual(report["score"], 0)
                self.assertEqual(report["stats"]["words"], 0)
                self.assertEqual(report["found_skills"], [])
                self.assertEqual(report["found_buzzwords"], [])


class TestScoring(unittest.TestCase):
    def test_score_always_within_bounds(self):
        cases = [
            "python " * 500,
            " ".join(BUZZWORDS) * 20 + "!" * 200,
            " ".join(SKILLS),
            "I have 99 years of experience!!!!!!!!!!",
            "a",
        ]
        for text in cases:
            with self.subTest(text=text[:30]):
                self.assertGreaterEqual(analyse(text)["score"], 0)
                self.assertLessEqual(analyse(text)["score"], 100)

    def test_deterministic(self):
        text = "Python developer, 5 years, Docker and SQL."
        self.assertEqual(analyse(text), analyse(text))

    def test_buzzwords_hurt(self):
        clean = "Built Python services with Docker and SQL over 5 years."
        cursed = clean + " A passionate proactive rockstar ninja guru."
        self.assertLess(analyse(cursed)["score"], analyse(clean)["score"])

    def test_verdict_matches_band(self):
        bands = [(95, "HIRE IMMEDIATELY"), (80, "STRONG YES"), (65, "PROBABLY FINE"),
                 (50, "HMMM"), (35, "NEEDS SEASONING"), (0, "BOLD CHOICE")]
        for text in ("python " * 300, " ".join(BUZZWORDS), "Docker Python SQL React Go Rust"):
            r = analyse(text)
            expected = next(v for t, v in bands if r["score"] >= t)
            self.assertEqual(r["verdict"], expected, msg=f"score={r['score']}")


class TestDetection(unittest.TestCase):
    def test_skills_need_word_boundaries(self):
        self.assertNotIn("go", analyse("I work at Google on Django.")["found_skills"])
        self.assertIn("go", analyse("I write Go daily.")["found_skills"])

    def test_skills_are_deduplicated_and_sorted(self):
        found = analyse("Python python PYTHON docker Docker")["found_skills"]
        self.assertEqual(found, ["docker", "python"])

    def test_years_are_summed(self):
        self.assertEqual(analyse("3 years here, 4 yrs there, 10+ years elsewhere")
                         ["stats"]["years_claimed"], 17)

    def test_vampire_note(self):
        notes = analyse("30 years at A. 30 years at B.")["notes"]
        self.assertTrue(any("vampire" in n for n in notes))

    def test_cursed_skills_get_a_comment(self):
        notes = analyse("Expert in PowerPoint and Excel.")["notes"]
        self.assertTrue(any("PowerPoint" in n for n in notes))
        self.assertTrue(any("Excel" in n for n in notes))

    def test_notes_never_empty(self):
        self.assertTrue(analyse("Wrote software. Shipped it. Went home.")["notes"])


class TestShape(unittest.TestCase):
    def test_response_contract(self):
        r = analyse("Python, SQL, Docker. 5 years.")
        self.assertEqual(set(r), {"score", "verdict", "roast", "stats",
                                  "found_skills", "found_buzzwords", "notes"})
        self.assertEqual(set(r["stats"]), {"words", "buzzwords", "skills", "years_claimed",
                                           "exclamations", "coffee_index", "reading_time_s"})
        self.assertEqual(r["stats"]["skills"], len(r["found_skills"]))
        self.assertEqual(r["stats"]["buzzwords"], len(r["found_buzzwords"]))

    def test_empty_matches_the_same_contract(self):
        self.assertEqual(set(analyse("")), set(analyse("Python")))
        self.assertEqual(set(analyse("")["stats"]), set(analyse("Python")["stats"]))

    def test_unicode_does_not_explode(self):
        r = analyse("Résumé: Python, 日本語, emoji 🚀, 3 years")
        self.assertGreater(r["stats"]["words"], 0)
        self.assertIn("python", r["found_skills"])


if __name__ == "__main__":
    unittest.main()
