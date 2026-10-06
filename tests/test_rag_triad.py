import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.rag_triad import (
    compute_answer_relevance,
    compute_context_relevance,
    compute_groundedness,
    evaluate_rag_dataset,
    evaluate_rag_triad,
)


class TestRAGTriad(unittest.TestCase):
    def test_context_relevance_high(self):
        query = "What is the policy for unauthenticated sidecars?"
        context = "Under DADA Vol 1 policy, unauthenticated sidecar daemons must be removed."
        cr = compute_context_relevance(query, context)
        self.assertGreaterEqual(cr, 0.70)

    def test_context_relevance_empty_context(self):
        query = "What is the policy?"
        cr = compute_context_relevance(query, "")
        self.assertEqual(cr, 0.0)

    def test_groundedness_grounded(self):
        context = "Harbor Ledger stores invoices for Mina. The total due is 1200 dollars."
        response = "Harbor Ledger stores invoices for Mina with 1200 dollars due."
        g = compute_groundedness(response, context)
        self.assertGreaterEqual(g, 0.75)

    def test_groundedness_hallucination(self):
        context = "Harbor Ledger is an invoicing tool."
        response = "Astronauts discovered ancient alien pyramids on the surface of Mars."
        g = compute_groundedness(response, context)
        self.assertLess(g, 0.40)

    def test_answer_relevance_high(self):
        query = "What is the due balance for Mina?"
        response = "The due balance for Mina is 1200 dollars."
        ar = compute_answer_relevance(query, response)
        self.assertGreaterEqual(ar, 0.70)

    def test_answer_relevance_evasive(self):
        query = "What is the due balance for Mina?"
        response = "I cannot answer this question as an AI."
        ar = compute_answer_relevance(query, response)
        self.assertLessEqual(ar, 0.20)

    def test_rag_triad_scoring_formula(self):
        # Masterplan formula: RAG Score = (1/3) * (CR + G + AR)
        score = evaluate_rag_triad(
            query="Summarize invoice INV-1001 for customer Mina Paperweight.",
            context="Invoice INV-1001 was issued to Mina Paperweight for 50 boxes of archival staples. The total amount due is $1,200.00.",
            response="Invoice INV-1001 issued to Mina Paperweight totals $1,200.00 for archival staples.",
        )
        expected_score = (1.0 / 3.0) * (score.context_relevance + score.groundedness + score.answer_relevance)
        self.assertAlmostEqual(score.score, expected_score, places=3)
        self.assertGreaterEqual(score.score, 0.80)
        self.assertFalse(score.is_hallucination())

    def test_rag_batch_evaluation(self):
        samples = [
            {
                "query": "Where is Harbor Ledger located?",
                "context": "Harbor Ledger runs on 127.0.0.1.",
                "response": "Harbor Ledger is located on 127.0.0.1.",
            },
            {
                "query": "What planets exist in alpha centauri?",
                "context": "Astronomers study Alpha Centauri using ground telescopes.",
                "response": "Seven crystal cities populated by reptilian beings thrive on Pluto.",
            },
        ]
        batch = evaluate_rag_dataset(samples, hallucination_threshold=0.70)
        self.assertEqual(batch.count, 2)
        self.assertEqual(batch.hallucination_count, 1)
        self.assertGreater(batch.mean_score, 0.0)


if __name__ == "__main__":
    unittest.main()
