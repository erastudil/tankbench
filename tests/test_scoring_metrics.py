import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.scoring import Score


class TestScoreMetrics(unittest.TestCase):
    def test_alive_ok_condition(self):
        # Test case where alive_ok should be True
        score_true = Score(alive_ran=5, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertTrue(score_true.alive_ok, "alive_ok should be True when alive_ran>0 and alive_failed==0")
        
        # Test case where alive_ok should be False (alive_ran == 0)
        score_false_ran = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score_false_ran.alive_ok, "alive_ok should be False when alive_ran==0")
        
        # Test case where alive_ok should be False (alive_failed > 0)
        score_false_failed = Score(alive_ran=5, alive_failed=1, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score_false_failed.alive_ok, "alive_ok should be False when alive_failed>0")
        
        # Test case where both conditions fail
        score_false_both = Score(alive_ran=0, alive_failed=1, rounds_ran=0, rounds_hits=0)
        self.assertFalse(score_false_both.alive_ok, "alive_ok should be False when both conditions fail")

    def test_blocked_ratio_no_hits(self):
        # Test blocked_ratio returns 1.0 when rounds_hits=0 and rounds_ran>0
        score = Score(alive_ran=0, alive_failed=0, rounds_ran=10, rounds_hits=0)
        self.assertEqual(
            score.blocked_ratio, 
            1.0, 
            "blocked_ratio should be 1.0 when rounds_hits=0 and rounds_ran>0"
        )
        
        # Additional edge case: rounds_ran=0 should return 0.0
        score_zero = Score(alive_ran=0, alive_failed=0, rounds_ran=0, rounds_hits=0)
        self.assertEqual(
            score_zero.blocked_ratio, 
            0.0, 
            "blocked_ratio should be 0.0 when rounds_ran=0"
        )

    def test_value_when_not_alive_ok(self):
        # Test value returns 0.0 when alive_ok is False
        # Case 1: alive_ran == 0
        score1 = Score(alive_ran=0, alive_failed=0, rounds_ran=5, rounds_hits=3)
        self.assertFalse(
            score1.alive_ok, 
            "alive_ok should be False when alive_ran==0"
        )
        self.assertEqual(
            score1.value, 
            0.0, 
            "value should be 0.0 when alive_ok is False"
        )
        
        # Case 2: alive_failed > 0
        score2 = Score(alive_ran=5, alive_failed=2, rounds_ran=5, rounds_hits=3)
        self.assertFalse(
            score2.alive_ok, 
            "alive_ok should be False when alive_failed>0"
        )
        self.assertEqual(
            score2.value, 
            0.0, 
            "value should be 0.0 when alive_ok is False"
        )
        
        # Case 3: both conditions fail
        score3 = Score(alive_ran=0, alive_failed=1, rounds_ran=5, rounds_hits=3)
        self.assertFalse(
            score3.alive_ok, 
            "alive_ok should be False when both conditions fail"
        )
        self.assertEqual(
            score3.value, 
            0.0, 
            "value should be 0.0 when alive_ok is False"
        )


if __name__ == "__main__":
    unittest.main()
