import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.ci_gate import (
    CIEvaluationGate,
    GateThresholds,
    compute_distribution_metrics,
)
from tankbench.cli import main


class TestCIEvaluationGate(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parents[1] / "fixtures"

    def test_distribution_metrics_identical(self):
        vals = [0.8, 0.85, 0.9, 0.95]
        res = compute_distribution_metrics(vals, vals)
        self.assertEqual(res["js_divergence"], 0.0)
        self.assertEqual(res["wasserstein_distance"], 0.0)

    def test_distribution_metrics_drift(self):
        base = [0.9, 0.95, 1.0]
        drifted = [0.1, 0.15, 0.2]
        res = compute_distribution_metrics(base, drifted)
        self.assertGreater(res["js_divergence"], 0.5)
        self.assertGreater(res["wasserstein_distance"], 0.6)

    def test_gate_candidate_passing(self):
        gate = CIEvaluationGate()
        cand = self.fixtures / "candidate_passing.json"
        base = self.fixtures / "golden_baseline.json"
        decision = gate.evaluate(candidate_data=cand, baseline_data=base)
        self.assertTrue(decision.passed)
        self.assertEqual(decision.status, "PASSED")
        self.assertEqual(decision.deployment_action, "PROCEED_CANARY_DEPLOYMENT")
        self.assertEqual(len(decision.failure_reasons), 0)

    def test_gate_candidate_failing_assertions(self):
        gate = CIEvaluationGate()
        cand = self.fixtures / "candidate_failing_assertions.json"
        base = self.fixtures / "golden_baseline.json"
        decision = gate.evaluate(candidate_data=cand, baseline_data=base)
        self.assertFalse(decision.passed)
        self.assertEqual(decision.status, "FAILED")
        self.assertEqual(decision.deployment_action, "TRIGGER_ROLLBACK")
        self.assertGreater(len(decision.failure_reasons), 0)

    def test_gate_candidate_hallucinating(self):
        gate = CIEvaluationGate()
        cand = self.fixtures / "candidate_hallucinating.json"
        base = self.fixtures / "golden_baseline.json"
        decision = gate.evaluate(candidate_data=cand, baseline_data=base)
        self.assertFalse(decision.passed)
        self.assertEqual(decision.status, "FAILED")
        self.assertEqual(decision.deployment_action, "TRIGGER_ROLLBACK")
        self.assertIn("hallucinated", str(decision.failure_reasons))

    def test_cli_gate_command_exit_code_zero(self):
        cand = str(self.fixtures / "candidate_passing.json")
        base = str(self.fixtures / "golden_baseline.json")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["gate", "--candidate", cand, "--baseline", base])
        self.assertEqual(ret, 0)
        self.assertIn("PROCEED_CANARY", buf.getvalue())

    def test_cli_gate_command_exit_code_one(self):
        cand = str(self.fixtures / "candidate_failing_assertions.json")
        base = str(self.fixtures / "golden_baseline.json")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["gate", "--candidate", cand, "--baseline", base])
        self.assertEqual(ret, 1)
        self.assertIn("TRIGGER_ROLLBACK", buf.getvalue())

    def test_cli_gate_json_output(self):
        cand = str(self.fixtures / "candidate_passing.json")
        base = str(self.fixtures / "golden_baseline.json")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["gate", "--candidate", cand, "--baseline", base, "--json"])
        self.assertEqual(ret, 0)
        parsed = json.loads(buf.getvalue())
        self.assertEqual(parsed["status"], "PASSED")
        self.assertEqual(parsed["deployment_action"], "PROCEED_CANARY_DEPLOYMENT")
        self.assertIn("metrics", parsed)


if __name__ == "__main__":
    unittest.main()
