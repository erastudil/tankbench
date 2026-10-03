import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.scoring import Score


class TestScoringMetrics(unittest.TestCase):
    def test_alive_ok_conditions(self):
        # alive_ok True only when alive_ran > 0 and alive_failed == 0
        self.assertFalse(Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0).alive_ok)
        self.assertTrue(Score(alive_ran=5, alive_failed=0, rounds_ran=0, rounds_hits=0).alive_ok)
        self.assertFalse(Score(alive_ran=5, alive_failed=1, rounds_ran=0, rounds_hits=0).alive_ok)
        self.assertFalse(Score(alive_ran=0, alive_failed=5, rounds_ran=0, rounds_hits=0).alive_ok)

    def test_blocked_ratio_when_no_hits(self):
        # blocked_ratio returns 1.0 when rounds_hits=0 and rounds_ran>0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 1.0)
        # Edge case: rounds_ran=0 should return 0.0 (not 1.0)
        score_zero = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertEqual(score_zero.blocked_ratio, 0.0)

    def test_value_zero_when_not_alive_ok(self):
        # value returns 0.0 when alive_ok is False
        # Case 1: alive_ran == 0
        score1 = Score(alive_ran=0, alive_failed=0, rounds_ran=5, rounds_hits=0)
        self.assertFalse(score1.alive_ok)
        self.assertEqual(score1.value, 0.0)
        # Case 2: alive_failed > 0
        score2 = Score(alive_ran=5, alive_failed=3, rounds_ran=5, rounds_hits=0)
        self.assertFalse(score2.alive_ok)
        self.assertEqual(score2.value, 0.0)
        # Case 3: alive_ok True but value 0.0 due to no rounds/measures (should not happen per spec, but we test)
        # Actually, if alive_ok True and rounds_ran==0 and measures_ran==0 -> value=0.0
        score3 = Score(alive_ran=5, alive_failed=0, rounds_ran=0, rounds_hits=0, measures_ran=0, measures_passed=0)
        self.assertTrue(score3.alive_ok)
        self.assertEqual(score3.value, 0.0)


if __name__ == "__main__":
    unittest.main()
