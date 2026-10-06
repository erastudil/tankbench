from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tankbench.idle_worker import (
    DEFAULT_SCHEDULE_PATTERN,
    IdleComputeWorker,
    IdleWorkerConfig,
    IdleWorkResult,
    WorkCategory,
    parse_rss_xml,
    run_worker_cli,
    validate_progen_statement,
)


class TestIdleComputeWorker(unittest.TestCase):
    def setUp(self) -> None:
        self.config = IdleWorkerConfig(sample_interval_s=0.0, backoff_initial_s=0.01, backoff_max_s=0.1)
        self.worker = IdleComputeWorker(self.config)

    def test_weighted_schedule_distribution(self) -> None:
        cats = [self.worker.next_category() for _ in range(20)]
        emap_count = cats.count(WorkCategory.EMAP_REPAIR)
        easylm_count = cats.count(WorkCategory.EASYLM_DISTILLATION)
        snowgate_count = cats.count(WorkCategory.SNOWGATE_DISCOURSE)
        tankbench_count = cats.count(WorkCategory.TANKBENCH_VERIFY)

        self.assertEqual(emap_count, 8)
        self.assertEqual(easylm_count, 8)
        self.assertEqual(snowgate_count, 2)
        self.assertEqual(tankbench_count, 2)

        self.assertEqual(cats[:10], DEFAULT_SCHEDULE_PATTERN)
        self.assertEqual(cats[10:], DEFAULT_SCHEDULE_PATTERN)

    def test_execute_emap_repair(self) -> None:
        res = self.worker.execute_emap_repair()
        self.assertEqual(res.category, WorkCategory.EMAP_REPAIR)
        self.assertTrue(res.success)
        self.assertTrue(res.item_id.startswith("emap_"))
        self.assertIn("repaired_gloss", res.output)
        self.assertIn("t1_form", res.output)
        self.assertIn("dewey", res.output)

    def test_execute_easylm_distillation(self) -> None:
        res = self.worker.execute_easylm_distillation()
        self.assertEqual(res.category, WorkCategory.EASYLM_DISTILLATION)
        self.assertTrue(res.success)
        self.assertTrue(res.item_id.startswith("distill_"))
        self.assertEqual(res.output["format"], "sharegpt_v3")
        self.assertEqual(len(res.output["conversations"]), 2)

    def test_parse_rss_xml(self) -> None:
        sample_xml = """<rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Frontier AI Benchmark Released</title>
                    <link>https://example.com/ai</link>
                    <description><![CDATA[<p>Detailed benchmark description.</p>]]></description>
                    <guid>guid-12345</guid>
                </item>
            </channel>
        </rss>"""
        items = parse_rss_xml(sample_xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Frontier AI Benchmark Released")
        self.assertEqual(items[0]["guid"], "guid-12345")
        self.assertIn("Detailed benchmark description.", items[0]["summary"])

    def test_execute_snowgate_turn_offline(self) -> None:
        config = IdleWorkerConfig(enable_live_rss=False)
        worker = IdleComputeWorker(config)
        res = worker.execute_snowgate_turn()

        self.assertEqual(res.category, WorkCategory.SNOWGATE_DISCOURSE)
        self.assertTrue(res.success)
        self.assertFalse(res.output["rss_seeded"])
        self.assertIn("greentext", res.output)

    def test_execute_snowgate_rss_seeded_and_deduplication(self) -> None:
        mock_items = [
            {"title": "Open Weight LLM Model Released", "link": "http://example.com/llm", "summary": "New model weights", "guid": "llm-001"},
            {"title": "Bitcoin Market Liquidity Invariant", "link": "http://example.com/btc", "summary": "Market analysis", "guid": "btc-002"},
        ]
        with tempfile.TemporaryDirectory() as td:
            guids_path = Path(td) / "seen_guids.json"
            config = IdleWorkerConfig(seen_guids_file=guids_path, enable_live_rss=True, rss_feeds=["http://mock.feed"])
            worker = IdleComputeWorker(config)

            with patch("tankbench.idle_worker.fetch_live_rss", return_value=list(mock_items)):
                # Turn 1: should consume item 1
                r1 = worker.execute_snowgate_turn()
                self.assertTrue(r1.output["rss_seeded"])
                self.assertEqual(r1.output["rss_metadata"]["guid"], "llm-001")
                self.assertEqual(r1.output["board"], "models")
                self.assertIn("llm-001", worker._seen_guids)

                # Turn 2: should consume item 2
                r2 = worker.execute_snowgate_turn()
                self.assertTrue(r2.output["rss_seeded"])
                self.assertEqual(r2.output["rss_metadata"]["guid"], "btc-002")
                self.assertEqual(r2.output["board"], "economics")
                self.assertIn("btc-002", worker._seen_guids)

                # Turn 3: all items seen, should fall back cleanly
                r3 = worker.execute_snowgate_turn()
                self.assertFalse(r3.output["rss_seeded"])

    def test_execute_tankbench_verify_and_fuzzing(self) -> None:
        res = self.worker.execute_tankbench_verify()
        self.assertEqual(res.category, WorkCategory.TANKBENCH_VERIFY)
        self.assertTrue(res.success)
        self.assertTrue(res.output["golden_set_passed"])
        self.assertTrue(res.output["assertion_fuzzing_graceful"])
        self.assertTrue(res.output["progen_invariant_fuzzing_passed"])
        self.assertGreaterEqual(res.output["progen_cases_evaluated"], 4)

    def test_progen_invariant_validator(self) -> None:
        # Valid statement
        self.assertEqual(validate_progen_statement("topic : valid comment"), [])
        self.assertEqual(validate_progen_statement("first : one\n\nsecond : two"), [])

        # P018 copula
        v_copula = validate_progen_statement("status : is unverified")
        self.assertTrue(any("P018_COPULA_DETECTED" in v for v in v_copula))

        # P001 parenthetical in prose
        v_paren = validate_progen_statement("directive : run now (with care)")
        self.assertTrue(any("P001_PARENTHETICAL_IN_PROSE" in v for v in v_paren))

        # Delimiter missing
        v_delim = validate_progen_statement("a : 1\nb : 2")
        self.assertIn("MISSING_BLANK_LINE_DELIMITER", v_delim)

        # Missing separator
        v_layout = validate_progen_statement("no colon present")
        self.assertTrue(any("INVALID_UNIT_LAYOUT" in v for v in v_layout))

    def test_priority_interruption_flag(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            flag_file = Path(td) / "PRIORITY_INTERRUPT"
            config = IdleWorkerConfig(priority_flag_file=flag_file, sample_interval_s=0.0)
            worker = IdleComputeWorker(config)

            self.assertFalse(worker.is_priority_interrupted())
            self.assertIsNotNone(worker.step())

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
        config = IdleWorkerConfig(max_cycles=10, sample_interval_s=0.0)
        worker = IdleComputeWorker(config)
        results = worker.run()
        self.assertEqual(len(results), 10)
        self.assertEqual(worker.cycle_count, 10)
        categories = [r.category for r in results]
        self.assertEqual(categories.count(WorkCategory.EMAP_REPAIR), 4)
        self.assertEqual(categories.count(WorkCategory.EASYLM_DISTILLATION), 4)
        self.assertEqual(categories.count(WorkCategory.SNOWGATE_DISCOURSE), 1)
        self.assertEqual(categories.count(WorkCategory.TANKBENCH_VERIFY), 1)

    def test_run_worker_cli_entrypoint(self) -> None:
        code = run_worker_cli(max_cycles=2, as_json=True)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
