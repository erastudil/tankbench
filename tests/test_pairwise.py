import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.pairwise import (
    PairwiseComparison,
    compute_verbosity_penalty,
    evaluate_pairwise,
    evaluate_single_pairwise,
)


class TestPairwiseEvaluation(unittest.TestCase):
    def test_position_bias_mitigation_neutralizes_first_position_bias(self):
        # A judge with extreme position bias always selects the first option ("A")
        def biased_first_judge(prompt: str, opt_a: str, opt_b: str) -> str:
            return "A"

        comp = PairwiseComparison(
            id="bias_test",
            prompt="Summarize invoice",
            candidate="Candidate response",
            baseline="Baseline response",
            optimal_length=10,
        )
        res = evaluate_single_pairwise(comp, judge_fn=biased_first_judge)
        # Forward pass prefers candidate (+1), reverse pass prefers baseline (-1)
        self.assertEqual(res.forward_preference, 1)
        self.assertEqual(res.reverse_preference, -1)
        # Position bias is completely neutralized to 0.0 (tie)
        self.assertEqual(res.mitigated_preference, 0.0)
        self.assertEqual(res.decision, "tie")

    def test_genuine_winner_consistent_across_permutations(self):
        # A judge that evaluates content and consistently prefers the candidate
        def smart_judge(prompt: str, opt_a: str, opt_b: str) -> str:
            if "Candidate" in opt_a:
                return "A"
            if "Candidate" in opt_b:
                return "B"
            return "TIE"

        comp = PairwiseComparison(
            id="smart_test",
            prompt="Summarize invoice",
            candidate="Candidate response with rich details",
            baseline="Short response",
            optimal_length=10,
        )
        res = evaluate_single_pairwise(comp, judge_fn=smart_judge)
        self.assertEqual(res.forward_preference, 1)
        self.assertEqual(res.reverse_preference, 1)
        self.assertEqual(res.mitigated_preference, 1.0)
        self.assertEqual(res.decision, "candidate")

    def test_verbosity_penalty_math(self):
        # Verbosity Penalty = (Length - Optimal) / Optimal
        # Optimal = 10 words, Candidate = 20 words -> penalty = (20 - 10) / 10 = 1.0
        penalty = compute_verbosity_penalty(output_length=20, optimal_length=10)
        self.assertEqual(penalty, 1.0)

        # Under optimal length -> penalty = 0.0
        no_penalty = compute_verbosity_penalty(output_length=8, optimal_length=10)
        self.assertEqual(no_penalty, 0.0)

    def test_pairwise_scoring_formula_with_verbosity_penalty(self):
        # Masterplan formula:
        # Pairwise Score = (1/M) * sum( Preference * (1 / (1 + lambda * Verbosity Penalty)) )
        # If Preference = 1.0, length = 20, optimal = 10, lambda = 0.5:
        # Penalty = 1.0, Multiplier = 1 / (1 + 0.5 * 1.0) = 1 / 1.5 = 0.6667
        # Adjusted Score = 1.0 * 0.6667 = 0.6667
        def pick_first(prompt: str, opt_a: str, opt_b: str) -> str:
            return "A" if "word" in opt_a else "B"

        comp = PairwiseComparison(
            id="item1",
            prompt="Explain",
            candidate="word " * 20,  # 20 words
            baseline="other",
            optimal_length=10,
        )
        score = evaluate_pairwise([comp], judge_fn=pick_first, lambda_penalty=0.5)
        self.assertEqual(score.total, 1)
        self.assertEqual(score.wins, 1)
        expected_score = 1.0 * (1.0 / (1.0 + 0.5 * 1.0))
        self.assertAlmostEqual(score.pairwise_score, expected_score, places=3)


if __name__ == "__main__":
    unittest.main()
