import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.scoring import Score


class TestScoringMetrics(unittest.TestCase):
    def test_alive_ok_true_when_alive_ran_positive_and_alive_failed_zero(self):
        """Test that alive_ok is True only when alive_ran > 0 and alive_failed == 0"""
        # Case where alive_ok should be True
        score = Score(alive_ran=1, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertTrue(score.alive_ok)

        # Case where alive_ran is 0, so alive_ok should be False
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score.alive_ok)

        # Case where alive_failed is > 0, so alive_ok should be False
        score = Score(alive_ran=1, alive_failed=1, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score.alive_ok)

        # Case where both conditions fail
        score = Score(alive_ran=0, alive_failed=1, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score.alive_ok)

    def test_blocked_ratio_returns_one_when_rounds_hits_is_zero_and_rounds_ran_positive(self):
        """Test that blocked_ratio returns 1.0 when rounds_hits is 0 and rounds_ran > 0"""
        score = Score(alive_ran=1, alive_failed=0, rounds_ran=5, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 1.0)

        # Test other cases to ensure normal behavior
        score = Score(alive_ran=1, alive_failed=0, rounds_ran=4, rounds_hits=2)
        self.assertEqual(score.blocked_ratio, 0.5)

        # Edge case where rounds_ran is 0
        score = Score(alive_ran=1, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 0.0)

    def test_value_returns_zero_when_alive_ok_is_false(self):
        """Test that value returns 0.0 when alive_ok is False"""
        # Case where alive_ok is False due to alive_failed > 0
        score = Score(alive_ran=1, alive_failed=1, rounds_ran=5, rounds_hits=0, measures_ran=0, measures_passed=0)
        self.assertFalse(score.alive_ok)
        self.assertEqual(score.value, 0.0)

        # Case where alive_ok is False due to alive_ran == 0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=5, rounds_hits=0, measures_ran=0, measures_passed=0)
        self.assertFalse(score.alive_ok)
        self.assertEqual(score.value, 0.0)

        # Verify that when alive_ok is True, value can be non-zero
        score = Score(alive_ran=1, alive_failed=0, rounds_ran=5, rounds_hits=0, measures_ran=0, measures_passed=0)
        self.assertTrue(score.alive_ok)
        self.assertEqual(score.value, 1.0)  # blocked_ratio would be 1.0


if __name__ == "__main__":
    unittest.main()

