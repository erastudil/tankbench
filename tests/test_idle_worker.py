from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tankbench.idle_worker import (
    IdleComputeWorker,
    IdleWorkerConfig,
    IdleWorkResult,
    WorkCategory,
    run_worker_cli,
)


class TestIdleComputeWorker(unittest.TestCase):
    def setUp(self) -> None:
        self.config = IdleWorkerConfig(sample_interval_s=0.0, backoff_initial_s=0.01, backoff_max_s=0.1)
        self.worker = IdleComputeWorker(self.config)

    def test_category_rotation_sequence(self) -> None:
        cats = [self.worker.next_category() for _ in range(8)]
        expected = [
            WorkCategory.EMAP_REPAIR,
            WorkCategory.SNOWGATE_DISCOURSE,
            WorkCategory.EASYLM_DISTILLATION,
            WorkCategory.TANKBENCH_VERIFY,
            WorkCategory.EMAP_REPAIR,
            WorkCategory.SNOWGATE_DISCOURSE,
            WorkCategory.EASYLM_DISTILLATION,
            WorkCategory.TANKBENCH_VERIFY,
        ]
        self.assertEqual(cats, expected)

    def test_execute_emap_repair(self) -> None:
        res = self.worker.execute_emap_repair()
        self.assertEqual(res.category, WorkCategory.EMAP_REPAIR)
        self.assertTrue(res.success)
        self.assertTrue(res.item_id.startswith("emap_"))
        self.assertIn("repaired_gloss", res.output)
        self.assertIn("t1_form", res.output)

    def test_execute_snowgate_turn(self) -> None:
        res = self.worker.execute_snowgate_turn()
        self.assertEqual(res.category, WorkCategory.SNOWGATE_DISCOURSE)
        self.assertTrue(res.success)
        self.assertTrue(res.item_id.startswith("snowgate_"))
        self.assertIn("board", res.output)
        self.assertIn("greentext", res.output)

    def test_execute_easylm_distillation(self) -> None:
        res = self.worker.execute_easylm_distillation()
        self.assertEqual(res.category, WorkCategory.EASYLM_DISTILLATION)
        self.assertTrue(res.success)
        self.assertTrue(res.item_id.startswith("distill_"))
        self.assertEqual(res.output["format"], "sharegpt_v3")
        self.assertEqual(len(res.output["conversations"]), 2)

    def test_execute_tankbench_verify(self) -> None:
        res = self.worker.execute_tankbench_verify()
        self.assertEqual(res.category, WorkCategory.TANKBENCH_VERIFY)
        self.assertTrue(res.success)
        self.assertTrue(res.item_id.startswith("tb_verify_"))
        self.assertTrue(res.output["all_passed"])

    def test_priority_interruption_flag(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            flag_file = Path(td) / "PRIORITY_INTERRUPT"
            config = IdleWorkerConfig(priority_flag_file=flag_file, sample_interval_s=0.0)
            worker = IdleComputeWorker(config)

            self.assertFalse(worker.is_priority_interrupted())
            self.assertIsNotNone(worker.step())

            # Trigger flag file creation
            flag_file.write_text("HIGH_PRIORITY_TASK_ACTIVE", encoding="utf-8")
            self.assertTrue(worker.is_priority_interrupted())
            res = worker.step()
            self.assertIsNone(res)

    def test_backoff_on_failure(self) -> None:
        with patch.object(self.worker, "execute_emap_repair", side_effect=RuntimeError("Endpoint 503 Service Unavailable")):
            init_backoff = self.worker.current_backoff
            res = self.worker.step()
            self.assertIsNotNone(res)
            self.assertFalse(res.success)
            self.assertIn("Endpoint 503", res.error)
            self.assertGreater(self.worker.current_backoff, init_backoff)

    def test_worker_run_cycles(self) -> None:
        config = IdleWorkerConfig(max_cycles=4, sample_interval_s=0.0)
        worker = IdleComputeWorker(config)
        results = worker.run()
        self.assertEqual(len(results), 4)
        self.assertEqual(worker.cycle_count, 4)
        categories = [r.category for r in results]
        self.assertEqual(
            categories,
            [
                WorkCategory.EMAP_REPAIR,
                WorkCategory.SNOWGATE_DISCOURSE,
                WorkCategory.EASYLM_DISTILLATION,
                WorkCategory.TANKBENCH_VERIFY,
            ],
        )

    def test_run_worker_cli_entrypoint(self) -> None:
        code = run_worker_cli(max_cycles=2, as_json=True)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
