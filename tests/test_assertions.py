import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.assertions import (
    AssertionType,
    assert_exact_match,
    assert_json_schema,
    assert_regex,
    evaluate_assertion,
    evaluate_assertions,
)


class TestDeterministicAssertions(unittest.TestCase):
    def test_exact_match_pass(self):
        res = assert_exact_match("  hello world  ", "hello world", strip=True)
        self.assertTrue(res.passed)
        self.assertEqual(res.assertion_type, AssertionType.EXACT_MATCH)

    def test_exact_match_case_insensitive(self):
        res = assert_exact_match("HeLLo", "hello", ignore_case=True)
        self.assertTrue(res.passed)

    def test_exact_match_fail(self):
        res = assert_exact_match("abc", "xyz")
        self.assertFalse(res.passed)
        self.assertIn("Expected 'xyz', got 'abc'", res.details)

    def test_regex_match_pass(self):
        res = assert_regex("Invoice INV-1001 dated 2026-09-15", r"INV-\d{4}")
        self.assertTrue(res.passed)
        self.assertEqual(res.assertion_type, AssertionType.REGEX)

    def test_regex_match_fail(self):
        res = assert_regex("No invoice numbers here", r"INV-\d{4}")
        self.assertFalse(res.passed)

    def test_regex_invalid_pattern(self):
        res = assert_regex("test", r"([a-z")
        self.assertFalse(res.passed)
        self.assertIn("Invalid regex", res.details)

    def test_json_schema_valid_dict(self):
        schema = {
            "type": "object",
            "required": ["status", "count"],
            "properties": {
                "status": {"type": "string"},
                "count": {"type": "integer"},
            },
        }
        data = {"status": "ok", "count": 42}
        res = assert_json_schema(data, schema)
        self.assertTrue(res.passed)
        self.assertEqual(res.assertion_type, AssertionType.JSON_SCHEMA)

    def test_json_schema_valid_string(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string"}},
        }
        json_str = '{"id": "inv_001"}'
        res = assert_json_schema(json_str, schema)
        self.assertTrue(res.passed)

    def test_json_schema_invalid_type(self):
        schema = {
            "type": "object",
            "required": ["count"],
            "properties": {"count": {"type": "integer"}},
        }
        json_str = '{"count": "not_an_int"}'
        res = assert_json_schema(json_str, schema)
        self.assertFalse(res.passed)

    def test_json_schema_malformed_json(self):
        schema = {"type": "object"}
        res = assert_json_schema("{broken json", schema)
        self.assertFalse(res.passed)
        self.assertIn("Malformed JSON", res.details)

    def test_evaluate_assertions_scoring_formula(self):
        # Masterplan formula: Assertion Score = (1/N) * sum(1 if passed else 0)
        specs = [
            {"type": "exact_match", "output": "A", "expected": "A"},
            {"type": "regex", "output": "ABC-123", "pattern": r"\w+-\d+"},
            {"type": "exact_match", "output": "Wrong", "expected": "Right"},
            {"type": "json_schema", "output": '{"ok": true}', "schema": {"type": "object", "required": ["ok"]}},
        ]
        score = evaluate_assertions(specs)
        self.assertEqual(score.total, 4)
        self.assertEqual(score.passed, 3)
        self.assertEqual(score.failed, 1)
        self.assertEqual(score.score, 0.75)
        self.assertFalse(score.passed_all)

    def test_evaluate_assertions_all_pass(self):
        specs = [
            {"type": "exact_match", "output": "Alpha", "expected": "Alpha"},
            {"type": "regex", "output": "Code 99", "pattern": r"Code \d+"},
        ]
        score = evaluate_assertions(specs)
        self.assertEqual(score.total, 2)
        self.assertEqual(score.passed, 2)
        self.assertEqual(score.score, 1.0)
        self.assertTrue(score.passed_all)


if __name__ == "__main__":
    unittest.main()
