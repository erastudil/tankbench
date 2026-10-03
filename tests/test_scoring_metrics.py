import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.scoring import Score


class TestScoringMetrics(unittest.TestCase):
    def test_alive_ok_conditions(self):
        # Test case where alive_ok should be True
        score = Score(alive_ran=5, alive_failed=0, rounds_ran=10, rounds_hits=3)
        self.assertTrue(score.alive_ok)

        # Test case where alive_ran is 0 -> alive_ok False
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=3)
        self.assertFalse(score.alive_ok)

        # Test case where alive_failed > 0 -> alive_ok False
        score = Score(alive_ran=5, alive_failed=1, rounds_ran=10, rounds_hits=3)
        self.assertFalse(score.alive_ok)

    def test_blocked_ratio_when_no_hits(self):
        # When rounds_hits is 0 and rounds_ran > 0, blocked_ratio should be 1.0
        score = Score(alive_ran=1, alive_failed=0, rounds_ran=5, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 1.0)

        # Edge case: rounds_ran is 0 -> blocked_ratio should be 0.0 (by implementation)
        score = Score(alive_ran=1, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 0.0)

    def test_value_when_alive_ok_false(self):
        # When alive_ok is False, value should be 0.0 regardless of other fields
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=5, measures_ran=5, measures_passed=5)
        self.assertEqual(score.value, 0.0)

        score = Score(alive_ran=5, alive_failed=1, rounds_ran=10, rounds_hits=0, measures_ran=0, measures_passed=0)
        self.assertEqual(score.value, 0.0)

        # When alive_ok is True, we test that value is not forced to 0.0 (but we don't test the exact value here)
        score = Score(alive_ran=5, alive_failed=0, rounds_ran=10, rounds_hits=0, measures_ran=0, measures_passed=0)
        self.assertNotEqual(score.value, 0.0)  # Because blocked_ratio is 1.0 and measures_ratio is 0.0 -> 0.5*1.0 + 0.5*0.0 = 0.5


if __name__ == "__main__":
    unittest.main()
