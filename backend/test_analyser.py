"""Tests for the science."""

import unittest

from analyser import BUZZWORDS, ROUNDS, SKILLS, analyse, compare


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

    def test_buzzwords_need_word_boundaries(self):
        self.assertNotIn("dynamic", analyse("Aerodynamics research, 3 years.")["found_buzzwords"])
        self.assertIn("dynamic", analyse("A dynamic and proactive lead.")["found_buzzwords"])

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


class TestCompare(unittest.TestCase):
    STRONG = "Python, Go, SQL, Docker, Kubernetes, Terraform, AWS. 8 years."
    WEAK = "Passionate proactive rockstar ninja guru!!!!! Synergy. PowerPoint."

    def test_better_cv_wins(self):
        r = compare(self.STRONG, self.WEAK)
        self.assertEqual(r["winner"], "a")
        self.assertEqual(r["verdict"], "CANDIDATE A")
        self.assertGreater(r["a"]["score"], r["b"]["score"])

    def test_swapping_sides_swaps_the_winner(self):
        forward = compare(self.STRONG, self.WEAK)
        backward = compare(self.WEAK, self.STRONG)
        self.assertEqual(backward["winner"], "b")
        self.assertEqual(forward["margin"], backward["margin"])
        self.assertEqual(forward["a"], backward["b"])

    def test_identical_cvs_are_a_dead_heat(self):
        r = compare(self.STRONG, self.STRONG)
        self.assertIsNone(r["winner"])
        self.assertEqual(r["verdict"], "DEAD HEAT")
        self.assertEqual(r["margin"], 0)
        self.assertTrue(all(rnd["winner"] == "tie" for rnd in r["rounds"]))

    def test_two_empties_get_their_own_verdict(self):
        r = compare("", "   ")
        self.assertEqual(r["verdict"], "TWO EMPTY CHAIRS")
        self.assertIsNone(r["winner"])

    def test_margin_is_the_score_gap(self):
        r = compare(self.STRONG, self.WEAK)
        self.assertEqual(r["margin"], abs(r["a"]["score"] - r["b"]["score"]))

    def test_rounds_cover_every_category(self):
        r = compare(self.STRONG, self.WEAK)
        self.assertEqual([rnd["key"] for rnd in r["rounds"]], [k for k, _, _, _ in ROUNDS])
        for rnd in r["rounds"]:
            with self.subTest(round=rnd["key"]):
                self.assertIn(rnd["winner"], {"a", "b", "tie"})

    def test_lower_is_better_rounds_are_inverted(self):
        r = compare("Python. Docker.", "Python. Docker. Synergy, leverage, disrupt.")
        buzz = next(rnd for rnd in r["rounds"] if rnd["key"] == "buzzwords")
        self.assertFalse(buzz["higher_is_better"])
        self.assertEqual(buzz["a"], 0)
        self.assertEqual(buzz["winner"], "a")

    def test_rounds_won_matches_the_rounds(self):
        r = compare(self.STRONG, self.WEAK)
        for side in ("a", "b"):
            with self.subTest(side=side):
                self.assertEqual(r["rounds_won"][side],
                                 sum(1 for rnd in r["rounds"] if rnd["winner"] == side))

    def test_skill_overlap_is_partitioned(self):
        r = compare("Python and Docker.", "Python and React.")
        self.assertEqual(r["shared_skills"], ["python"])
        self.assertEqual(r["only_a"], ["docker"])
        self.assertEqual(r["only_b"], ["react"])

    def test_deterministic(self):
        self.assertEqual(compare(self.STRONG, self.WEAK), compare(self.STRONG, self.WEAK))

    def test_compare_contract(self):
        r = compare(self.STRONG, self.WEAK)
        self.assertEqual(set(r), {"a", "b", "winner", "verdict", "roast", "margin",
                                  "rounds", "rounds_won", "shared_skills",
                                  "only_a", "only_b", "notes"})
        self.assertEqual(set(r["a"]), set(analyse(self.STRONG)))
        self.assertTrue(r["notes"])

    def test_none_is_tolerated_like_analyse(self):
        r = compare(None, None)
        self.assertEqual(r["verdict"], "TWO EMPTY CHAIRS")


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
