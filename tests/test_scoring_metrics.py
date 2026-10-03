import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.scoring import Score


class TestScoringMetrics(unittest.TestCase):
    def test_alive_ok_conditions(self):
        # alive_ok should be True only when alive_ran > 0 and alive_failed == 0
        self.assertTrue(Score(alive_ran=1, alive_failed=0, rounds_ran=0, rounds_hits=0).alive_ok)
        self.assertFalse(Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0).alive_ok)
        self.assertFalse(Score(alive_ran=1, alive_failed=1, rounds_ran=0, rounds_hits=0).alive_ok)
        self.assertFalse(Score(alive_ran=0, alive_failed=1, rounds_ran=0, rounds_hits=0).alive_ok)

    def test_blocked_ratio_when_no_hits(self):
        # blocked_ratio should be 1.0 when rounds_hits is 0 and rounds_ran > 0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=5, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 1.0)
        # Edge case: rounds_ran == 0 should return 0.0 (already covered by implementation)
        score_zero = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertEqual(score_zero.blocked_ratio, 0.0)

    def test_value_when_alive_ok_false(self):
        # value should return 0.0 when alive_ok is False
        score_dead = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=5)
        self.assertFalse(score_dead.alive_ok)
        self.assertEqual(score_dead.value, 0.0)

        score_failed = Score(alive_ran=5, alive_failed=1, rounds_ran=10, rounds_hits=5)
        self.assertFalse(score_failed.alive_ok)
        self.assertEqual(score_failed.value, 0.0)


if __name__ == "__main__":
    unittest.main()
