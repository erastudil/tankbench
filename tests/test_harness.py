from __future__ import annotations

import unittest
from pathlib import Path

from tankbench.harness import grade, repo_root


class Harness(unittest.TestCase):
    def test_baseline_all_rounds_hit(self):
        score = grade(expect_baseline=True)
        self.assertTrue(score.alive_ok)
        self.assertEqual(score.rounds_hits, score.rounds_ran)
        self.assertGreater(score.rounds_ran, 8)
        self.assertEqual(score.value, 0.0)

    def test_dead_patient_scores_zero(self):
        dead = repo_root() / "fixtures" / "dead" / "app.py"
        score = grade(app=dead)
        self.assertFalse(score.alive_ok)
        self.assertEqual(score.value, 0.0)


if __name__ == "__main__":
    unittest.main()
