from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from tankbench.scoring import Score


class TestScoringMetrics(unittest.TestCase):
    def test_not_alive_score(self):
        """Cover not-alive scores: alive_ran == 0 or alive_failed > 0 gives value == 0.0."""
        # alive_ran == 0
        s_untested = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=0)
        self.assertFalse(s_untested.alive_ok)
        self.assertEqual(s_untested.value, 0.0)

        # alive_failed > 0
        s_failed = Score(alive_ran=5, alive_failed=1, rounds_ran=10, rounds_hits=0)
        self.assertFalse(s_failed.alive_ok)
        self.assertEqual(s_failed.value, 0.0)

    def test_partial_blocked_ratio(self):
        """Cover a partial blocked ratio."""
        s = Score(alive_ran=1, alive_failed=0, rounds_ran=10, rounds_hits=3)
        self.assertEqual(s.rounds_blocked, 7)
        self.assertAlmostEqual(s.blocked_ratio, 0.7)

    def test_measures_ran_zero_shortcut(self):
        """Cover measures_ran == 0 with value == 1.0 when blocked_ratio is 1.0."""
        s = Score(alive_ran=1, alive_failed=0, rounds_ran=10, rounds_hits=0, measures_ran=0)
        self.assertTrue(s.alive_ok)
        self.assertEqual(s.blocked_ratio, 1.0)
        self.assertEqual(s.measures_ran, 0)
        self.assertEqual(s.value, 1.0)

    def test_positive_composite_score(self):
        """Cover one positive composite score combining blocked_ratio and measures_ratio."""
        # 50% offensive backdoor resistance (blocked_ratio 0.8) + 50% preventative armory tooling (measures_ratio 0.5)
        # value = (0.5 * 0.8) + (0.5 * 0.5) = 0.40 + 0.25 = 0.65
        s = Score(
            alive_ran=1,
            alive_failed=0,
            rounds_ran=10,
            rounds_hits=2,
            measures_ran=4,
            measures_passed=2,
        )
        self.assertTrue(s.alive_ok)
        self.assertAlmostEqual(s.blocked_ratio, 0.8)
        self.assertAlmostEqual(s.measures_ratio, 0.5)
        self.assertAlmostEqual(s.value, 0.65)


if __name__ == "__main__":
    unittest.main()
