"""Tests for the science."""

import unittest
from unittest import mock

import analyser
import biometrics
import llm
from analyser import BUZZWORDS, SKILLS, analyse


class TestEmpty(unittest.TestCase):
    def test_blank_input_is_its_own_verdict(self):
        for text in ("", "   \n\t ", None, "!!! 123 ---"):
            with self.subTest(text=text):
                r = analyse(text)
                self.assertEqual(r["verdict"], "EMPTY")
                self.assertEqual(r["score"], 0)
                self.assertEqual(r["stats"]["words"], 0)
                self.assertEqual(r["found_skills"], [])
                self.assertEqual(r["found_buzzwords"], [])
                self.assertEqual(r["biometrics"]["heart_rate_bpm"], 0)
                self.assertEqual(r["llm"]["score"], 0)


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


class TestBiometrics(unittest.TestCase):
    def test_reading_is_deterministic(self):
        text = "Python developer, 5 years, Docker and SQL."
        self.assertEqual(biometrics.read(text), biometrics.read(text))

    def test_vitals_stay_in_believable_ranges(self):
        for text in ("python " * 400, " ".join(BUZZWORDS) + "!" * 50, "a"):
            with self.subTest(text=text[:20]):
                r = biometrics.read(text, stress=99)
                self.assertLessEqual(r["palm_sweat_index"], 10)
                self.assertLessEqual(r["honesty_tremor"], 1.0)
                self.assertGreater(r["confidence"], 0)
                self.assertTrue(r["notes"])

    def test_stress_raises_the_pulse(self):
        text = "Built Python services with Docker."
        self.assertGreater(biometrics.read(text, stress=8)["heart_rate_bpm"],
                           biometrics.read(text, stress=0)["heart_rate_bpm"])

    def test_empty_reading_is_not_shared_state(self):
        first = biometrics.read("")
        first["notes"].append("mutated")
        self.assertEqual(len(biometrics.read("")["notes"]), 1)

    def test_analyse_attaches_a_reading(self):
        r = analyse("Python, Docker, 4 years.")
        self.assertEqual(r["biometrics"]["sensor"], biometrics.SENSOR_ID)
        self.assertEqual(len(r["biometrics"]["ridge_signature"]), 10)


class TestLlmGrader(unittest.TestCase):
    def test_grade_is_deterministic(self):
        text = "Python developer, 5 years, Docker and SQL."
        self.assertEqual(llm.grade(text, skills=3), llm.grade(text, skills=3))

    def test_score_stays_within_bounds(self):
        cases = [(0, 20, 40, 0.1), (25, 0, 0, 1.0), (3, 2, 1, 0.5)]
        for skills, buzz, excl, ratio in cases:
            with self.subTest(skills=skills, buzzwords=buzz):
                r = llm.grade("a curriculum", skills=skills, buzzwords=buzz,
                              exclamations=excl, unique_ratio=ratio)
                self.assertGreaterEqual(r["score"], 0)
                self.assertLessEqual(r["score"], 100)

    def test_buzzwords_lower_the_model_score(self):
        text = "Built Python services with Docker and SQL."
        clean = llm.grade(text, skills=3, unique_ratio=0.9)["score"]
        cursed = llm.grade(text, skills=3, buzzwords=4, unique_ratio=0.9)["score"]
        self.assertLess(cursed, clean)

    def test_prompt_contains_the_curriculum(self):
        prompt = llm.build_prompt("Python, 5 years")
        self.assertIn("Python, 5 years", prompt)
        self.assertIn("<curriculum>", prompt)

    def test_nothing_is_sent_anywhere(self):
        """The 'LLM' is local. If this ever opens a socket, that is a bug."""
        self.assertEqual(llm.BACKEND, "offline-stub")
        with mock.patch("socket.socket", side_effect=AssertionError("network!")):
            llm.grade("Python, Docker, 5 years", skills=2, unique_ratio=0.8)

    def test_analyse_blends_both_scores(self):
        r = analyse("Python, SQL, Docker. 5 years of shipping services.")
        blended = round(r["stats"]["formula_score"] * (1 - analyser.LLM_WEIGHT)
                        + r["stats"]["llm_score"] * analyser.LLM_WEIGHT)
        self.assertEqual(r["score"], max(0, min(100, blended)))
        self.assertEqual(r["stats"]["llm_score"], r["llm"]["score"])


class TestShape(unittest.TestCase):
    def test_response_contract(self):
        r = analyse("Python, SQL, Docker. 5 years.")
        self.assertEqual(set(r), {"score", "verdict", "roast", "stats", "found_skills",
                                  "found_buzzwords", "notes", "biometrics", "llm"})
        self.assertEqual(set(r["stats"]), {"words", "buzzwords", "skills", "years_claimed",
                                           "exclamations", "coffee_index", "reading_time_s",
                                           "formula_score", "llm_score"})
        self.assertEqual(r["stats"]["skills"], len(r["found_skills"]))
        self.assertEqual(r["stats"]["buzzwords"], len(r["found_buzzwords"]))

    def test_empty_matches_the_same_contract(self):
        self.assertEqual(set(analyse("")), set(analyse("Python")))
        self.assertEqual(set(analyse("")["stats"]), set(analyse("Python")["stats"]))
        self.assertEqual(set(analyse("")["llm"]), set(analyse("Python")["llm"]))
        self.assertEqual(set(analyse("")["biometrics"]), set(analyse("Python")["biometrics"]))

    def test_unicode_does_not_explode(self):
        r = analyse("Résumé: Python, 日本語, emoji 🚀, 3 years")
        self.assertGreater(r["stats"]["words"], 0)
        self.assertIn("python", r["found_skills"])


if __name__ == "__main__":
    unittest.main()
