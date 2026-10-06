from __future__ import annotations

import unittest

from tankbench.reset_blast import (
    BlastConfig,
    BlastResult,
    QuotaProvider,
    ResetDayBlastRunner,
    run_blast_cli,
)


class TestResetDayBlast(unittest.TestCase):
    def test_unauthorized_blast_blocked_by_safety_fence(self) -> None:
        config = BlastConfig(blast_authorized=False, dry_run=False)
        runner = ResetDayBlastRunner(config)
        res = runner.execute_blast()

        self.assertFalse(res.authorized)
        self.assertFalse(res.safety_fence_passed)
        self.assertEqual(res.status, "BLOCKED_FENCE")
        self.assertIn("BLOCKED: Blast operation requires explicit authorization", res.fence_violation)
        self.assertEqual(res.tankbench_eval_count, 0)
        self.assertEqual(res.distillation_sample_count, 0)
        self.assertEqual(res.emap_audited_nodes, 0)

    def test_unmetered_payg_blocked_by_ceiling_fence(self) -> None:
        unmetered_provider = QuotaProvider(
            name="UncappedPayAsYouGo",
            reset_schedule="none",
            hours_until_reset=0.0,
            has_ceiling=False,
            plan_name="Raw Credit Card Metered",
        )
        config = BlastConfig(
            blast_authorized=True,
            providers=[unmetered_provider],
            enforce_ceiling_check=True,
        )
        runner = ResetDayBlastRunner(config)
        res = runner.execute_blast()

        self.assertTrue(res.authorized)
        self.assertFalse(res.safety_fence_passed)
        self.assertEqual(res.status, "BLOCKED_FENCE")
        self.assertIn("unmetered pay-as-you-go without subscription ceiling", res.fence_violation)

    def test_dry_run_mode(self) -> None:
        config = BlastConfig(blast_authorized=False, dry_run=True)
        runner = ResetDayBlastRunner(config)
        res = runner.execute_blast()

        self.assertTrue(res.safety_fence_passed)
        self.assertEqual(res.status, "DRY_RUN")
        self.assertTrue(res.telemetry["dry_run"])
        self.assertIn("OpenRouter", res.telemetry["target_providers"])

    def test_authorized_blast_execution(self) -> None:
        config = BlastConfig(
            blast_authorized=True,
            max_eval_items=3,
            max_distill_items=3,
            max_emap_nodes=50,
        )
        runner = ResetDayBlastRunner(config)
        res = runner.execute_blast()

        self.assertTrue(res.authorized)
        self.assertTrue(res.safety_fence_passed)
        self.assertEqual(res.status, "EXECUTED")
        self.assertIsNone(res.fence_violation)
        self.assertEqual(res.tankbench_eval_count, 3)
        self.assertEqual(res.distillation_sample_count, 3)
        self.assertEqual(res.emap_audited_nodes, 50)
        self.assertIn("tankbench", res.telemetry)
        self.assertIn("distillation", res.telemetry)
        self.assertIn("emap", res.telemetry)

    def test_cli_runner_exit_codes(self) -> None:
        # Unauthorized fails closed with exit code 1
        code_blocked = run_blast_cli(blast_authorized=False, as_json=True)
        self.assertEqual(code_blocked, 1)

        # Authorized passes with exit code 0
        code_auth = run_blast_cli(blast_authorized=True, as_json=True)
        self.assertEqual(code_auth, 0)

        # Dry run passes with exit code 0
        code_dry = run_blast_cli(dry_run=True, as_json=True)
        self.assertEqual(code_dry, 0)

    def test_serialization_to_dict(self) -> None:
        qp = QuotaProvider("TestProvider", "monthly_1st", 2.5, True, "Test Plan")
        qp_dict = qp.to_dict()
        self.assertEqual(qp_dict["name"], "TestProvider")
        self.assertEqual(qp_dict["hours_until_reset"], 2.5)
        self.assertTrue(qp_dict["has_ceiling"])

        res = BlastResult(
            authorized=True,
            safety_fence_passed=True,
            status="EXECUTED",
            tankbench_eval_count=2,
            distillation_sample_count=2,
            emap_audited_nodes=20,
        )
        res_dict = res.to_dict()
        self.assertEqual(res_dict["status"], "EXECUTED")
        self.assertEqual(res_dict["tankbench_eval_count"], 2)


if __name__ == "__main__":
    unittest.main()
