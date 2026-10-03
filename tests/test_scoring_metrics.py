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
        score = Score(alive_ran=5, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertTrue(score.alive_ok)

        # alive_ran == 0 -> False
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score.alive_ok)

        # alive_failed > 0 -> False
        score = Score(alive_ran=5, alive_failed=1, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score.alive_ok)

        # both conditions fail -> False
        score = Score(alive_ran=0, alive_failed=1, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score.alive_ok)

    def test_blocked_ratio_when_no_hits(self):
        # blocked_ratio returns 1.0 when rounds_hits=0 and rounds_ran>0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 1.0)

        # edge case: rounds_ran=0 -> blocked_ratio=0.0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 0.0)

        # mixed case: some hits
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=3)
        self.assertEqual(score.blocked_ratio, 0.7)

    def test_value_zero_when_not_alive_ok(self):
        # value returns 0.0 when alive_ok is False
        # Case 1: alive_ran == 0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=5, rounds_hits=0)
        self.assertFalse(score.alive_ok)
        self.assertEqual(score.value, 0.0)

        # Case 2: alive_failed > 0
        score = Score(alive_ran=5, alive_failed=2, rounds_ran=5, rounds_hits=0)
        self.assertFalse(score.alive_ok)
        self.assertEqual(score.value, 0.0)

        # Case 3: both conditions fail
        score = Score(alive_ran=0, alive_failed=2, rounds_ran=5, rounds_hits=0)
        self.assertFalse(score.alive_ok)
        self.assertEqual(score.value, 0.0)

        # Even with rounds_ran>0 and rounds_hits=0, if alive_ok is False -> value=0.0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=5, rounds_hits=0)
        self.assertFalse(score.alive_ok)
        self.assertEqual(score.value, 0.0)


if __name__ == "__main__":
    unittest.main()
