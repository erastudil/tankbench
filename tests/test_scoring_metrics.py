import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.scoring import Score


class TestScoringMetrics(unittest.TestCase):
    def test_alive_ok_conditions(self):
        # alive_ok is True only if alive_ran > 0 and alive_failed == 0
        score1 = Score(alive_ran=1, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertTrue(score1.alive_ok)
        
        score2 = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score2.alive_ok)
        
        score3 = Score(alive_ran=5, alive_failed=1, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score3.alive_ok)
        
        score4 = Score(alive_ran=0, alive_failed=5, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score4.alive_ok)

    def test_blocked_ratio_when_no_hits_and_some_rounds(self):
        # blocked_ratio returns 1.0 when rounds_hits is 0 and rounds_ran > 0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=0)
        self.assertEqual(score.blocked_ratio, 1.0)
        
        # Additional edge case: rounds_ran == 0 should return 0.0 (not 1.0)
        score_zero_rounds = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertEqual(score_zero_rounds.blocked_ratio, 0.0)

    def test_value_zero_when_not_alive_ok(self):
        # value returns 0.0 when alive_ok is False
        # Case 1: alive_ran == 0
        score1 = Score(alive_ran=0, alive_failed=0, rounds_ran=5, rounds_hits=3)
        self.assertFalse(score1.alive_ok)
        self.assertEqual(score1.value, 0.0)
        
        # Case 2: alive_failed > 0
        score2 = Score(alive_ran=5, alive_failed=2, rounds_ran=5, rounds_hits=3)
        self.assertFalse(score2.alive_ok)
        self.assertEqual(score2.value, 0.0)
        
        # Case 3: both conditions
        score3 = Score(alive_ran=0, alive_failed=2, rounds_ran=5, rounds_hits=3)
        self.assertFalse(score3.alive_ok)
        self.assertEqual(score3.value, 0.0)


if __name__ == "__main__":
    unittest.main()
