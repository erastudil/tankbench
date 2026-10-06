from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Union

try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False


class AssertionType:
    EXACT_MATCH = "exact_match"
    REGEX = "regex"
    JSON_SCHEMA = "json_schema"


@dataclass
class AssertionResult:
    name: str
    assertion_type: str
    passed: bool
    details: str = ""
    expected: Any = None
    actual: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "assertion_type": self.assertion_type,
            "passed": self.passed,
            "details": self.details,
            "expected": str(self.expected) if self.expected is not None else None,
            "actual": str(self.actual) if self.actual is not None else None,
        }


@dataclass
class AssertionScore:
    total: int
    passed: int
    failed: int
    score: float
    results: list[AssertionResult] = field(default_factory=list)

    @property
    def passed_all(self) -> bool:
        return self.failed == 0 and self.total > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "score": round(self.score, 4),
            "passed_all": self.passed_all,
            "results": [r.to_dict() for r in self.results],
        }


def assert_exact_match(
    output: Any,
    expected: Any,
    *,
    name: str = "exact_match",
    strip: bool = True,
    ignore_case: bool = False,
    normalize_whitespace: bool = False,
) -> AssertionResult:
    str_out = str(output) if output is not None else ""
    str_exp = str(expected) if expected is not None else ""

    if strip:
        str_out = str_out.strip()
        str_exp = str_exp.strip()

    if normalize_whitespace:
        str_out = re.sub(r"\s+", " ", str_out)
        str_exp = re.sub(r"\s+", " ", str_exp)

    if ignore_case:
        str_out = str_out.lower()
        str_exp = str_exp.lower()

    passed = str_out == str_exp
    details = "Exact match verified" if passed else f"Expected '{expected}', got '{output}'"
    return AssertionResult(
        name=name,
        assertion_type=AssertionType.EXACT_MATCH,
        passed=passed,
        details=details,
        expected=expected,
        actual=output,
    )


def assert_regex(
    output: Any,
    pattern: Union[str, re.Pattern],
    *,
    name: str = "regex_match",
    flags: int = 0,
) -> AssertionResult:
    str_out = str(output) if output is not None else ""
    pat_str = pattern.pattern if isinstance(pattern, re.Pattern) else str(pattern)

    try:
        compiled = pattern if isinstance(pattern, re.Pattern) else re.compile(pat_str, flags=flags)
        match = compiled.search(str_out)
        passed = match is not None
        details = f"Pattern '{pat_str}' matched" if passed else f"Pattern '{pat_str}' not found in output"
    except re.error as err:
        passed = False
        details = f"Invalid regex pattern '{pat_str}': {err}"

    return AssertionResult(
        name=name,
        assertion_type=AssertionType.REGEX,
        passed=passed,
        details=details,
        expected=pat_str,
        actual=str_out,
    )


def _validate_schema_fallback(data: Any, schema: dict[str, Any]) -> tuple[bool, str]:
    expected_type = schema.get("type")
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    if expected_type and expected_type in type_map:
        if not isinstance(data, type_map[expected_type]):
            return False, f"Expected type {expected_type}, got {type(data).__name__}"

    if isinstance(data, dict):
        required = schema.get("required", [])
        for req in required:
            if req not in data:
                return False, f"Missing required property: {req}"
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                valid, msg = _validate_schema_fallback(data[prop_name], prop_schema)
                if not valid:
                    return False, f"Property '{prop_name}': {msg}"
    elif isinstance(data, list) and "items" in schema:
        item_schema = schema["items"]
        for idx, item in enumerate(data):
            valid, msg = _validate_schema_fallback(item, item_schema)
            if not valid:
                return False, f"Item [{idx}]: {msg}"

    return True, "Schema valid"


def assert_json_schema(
    output: Any,
    schema: dict[str, Any],
    *,
    name: str = "json_schema_validity",
) -> AssertionResult:
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as err:
            return AssertionResult(
                name=name,
                assertion_type=AssertionType.JSON_SCHEMA,
                passed=False,
                details=f"Malformed JSON: {err}",
                expected=schema,
                actual=output,
            )
    else:
        parsed = output

    if _HAS_JSONSCHEMA:
        try:
            jsonschema.validate(instance=parsed, schema=schema)
            passed = True
            details = "JSON Schema validation succeeded"
        except jsonschema.ValidationError as err:
            passed = False
            details = f"JSON Schema validation error: {err.message}"
        except jsonschema.SchemaError as err:
            passed = False
            details = f"Invalid JSON Schema: {err.message}"
    else:
        passed, details = _validate_schema_fallback(parsed, schema)

    return AssertionResult(
        name=name,
        assertion_type=AssertionType.JSON_SCHEMA,
        passed=passed,
        details=details,
        expected=schema,
        actual=parsed,
    )


@dataclass
class AssertionSpec:
    name: str
    assertion_type: str
    output: Any = None
    expected: Any = None
    pattern: Union[str, re.Pattern, None] = None
    schema: Union[dict[str, Any], None] = None
    strip: bool = True
    ignore_case: bool = False
    normalize_whitespace: bool = False
    flags: int = 0


def evaluate_assertion(spec: Union[AssertionSpec, dict[str, Any]], default_output: Any = None) -> AssertionResult:
    if isinstance(spec, dict):
        a_type = spec.get("type") or spec.get("assertion_type", AssertionType.EXACT_MATCH)
        a_type = a_type.lower()
        if a_type in ("exact", "exact_match"):
            a_type = AssertionType.EXACT_MATCH
        elif a_type in ("regex", "pattern"):
            a_type = AssertionType.REGEX
        elif a_type in ("json", "schema", "json_schema"):
            a_type = AssertionType.JSON_SCHEMA

        spec = AssertionSpec(
            name=spec.get("name", "assertion"),
            assertion_type=a_type,
            output=spec.get("output"),
            expected=spec.get("expected"),
            pattern=spec.get("pattern"),
            schema=spec.get("schema"),
            strip=spec.get("strip", True),
            ignore_case=spec.get("ignore_case", False),
            normalize_whitespace=spec.get("normalize_whitespace", False),
            flags=spec.get("flags", 0),
        )

    out = spec.output if spec.output is not None else default_output

    if spec.assertion_type == AssertionType.EXACT_MATCH:
        return assert_exact_match(
            out,
            spec.expected,
            name=spec.name,
            strip=spec.strip,
            ignore_case=spec.ignore_case,
            normalize_whitespace=spec.normalize_whitespace,
        )
    elif spec.assertion_type == AssertionType.REGEX:
        pattern = spec.pattern if spec.pattern is not None else str(spec.expected)
        return assert_regex(out, pattern, name=spec.name, flags=spec.flags)
    elif spec.assertion_type == AssertionType.JSON_SCHEMA:
        schema = spec.schema if spec.schema is not None else spec.expected
        return assert_json_schema(out, schema or {}, name=spec.name)
    else:
        return AssertionResult(
            name=spec.name,
            assertion_type=spec.assertion_type,
            passed=False,
            details=f"Unknown assertion type: {spec.assertion_type}",
            expected=spec.expected,
            actual=out,
        )


def evaluate_assertions(
    specs: list[Union[AssertionSpec, dict[str, Any]]],
    default_output: Any = None,
) -> AssertionScore:
    """Evaluate deterministic unit assertions and calculate score.

    Assertion Score = (1 / N) * sum(1 if passed else 0)
    """
    if not specs:
        return AssertionScore(total=0, passed=0, failed=0, score=1.0, results=[])

    results: list[AssertionResult] = []
    passed_count = 0
    for s in specs:
        res = evaluate_assertion(s, default_output=default_output)
        results.append(res)
        if res.passed:
            passed_count += 1

    total = len(specs)
    failed_count = total - passed_count
    score = passed_count / total if total > 0 else 0.0

    return AssertionScore(
        total=total,
        passed=passed_count,
        failed=failed_count,
        score=score,
        results=results,
    )
