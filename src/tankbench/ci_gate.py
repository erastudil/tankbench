from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

from tankbench.assertions import AssertionScore, evaluate_assertions
from tankbench.pairwise import PairwiseScore, evaluate_pairwise
from tankbench.rag_triad import RAGBatchScore, evaluate_rag_dataset


def compute_distribution_metrics(
    baseline_values: list[float],
    candidate_values: list[float],
    num_bins: int = 10,
) -> dict[str, float]:
    """Calculate statistical distribution comparison metrics: JS divergence and Wasserstein distance.

    Returns JS divergence bounded in [0.0, 1.0] and Wasserstein distance.
    """
    if not baseline_values or not candidate_values:
        return {"js_divergence": 0.0, "wasserstein_distance": 0.0}

    # 1. 1D Wasserstein distance (Earth Mover's Distance)
    b_sorted = sorted(baseline_values)
    c_sorted = sorted(candidate_values)
    n_b = len(b_sorted)
    n_c = len(c_sorted)

    # Calculate empirical CDF difference integral
    all_vals = sorted(set(b_sorted + c_sorted))
    wasserstein = 0.0
    if len(all_vals) > 1:
        cdf_b = 0.0
        cdf_c = 0.0
        idx_b = 0
        idx_c = 0
        for i in range(len(all_vals) - 1):
            val = all_vals[i]
            next_val = all_vals[i + 1]
            while idx_b < n_b and b_sorted[idx_b] <= val:
                idx_b += 1
            while idx_c < n_c and c_sorted[idx_c] <= val:
                idx_c += 1
            cdf_b = idx_b / n_b
            cdf_c = idx_c / n_c
            wasserstein += abs(cdf_b - cdf_c) * (next_val - val)

    # 2. Jensen-Shannon Divergence
    min_val = min(b_sorted[0], c_sorted[0])
    max_val = max(b_sorted[-1], c_sorted[-1])
    if math.isclose(min_val, max_val):
        return {"js_divergence": 0.0, "wasserstein_distance": round(wasserstein, 4)}

    step = (max_val - min_val) / num_bins
    p_counts = [0.0] * num_bins
    q_counts = [0.0] * num_bins

    for v in b_sorted:
        b_idx = min(int((v - min_val) / step), num_bins - 1)
        p_counts[b_idx] += 1.0

    for v in c_sorted:
        c_idx = min(int((v - min_val) / step), num_bins - 1)
        q_counts[c_idx] += 1.0

    # Smooth distributions
    eps = 1e-8
    p = [(c + eps) / (n_b + eps * num_bins) for c in p_counts]
    q = [(c + eps) / (n_c + eps * num_bins) for c in q_counts]
    m = [0.5 * (p[i] + q[i]) for i in range(num_bins)]

    def kl_div(dist_a: list[float], dist_b: list[float]) -> float:
        return sum(dist_a[i] * math.log2(dist_a[i] / dist_b[i]) for i in range(len(dist_a)))

    js_div = 0.5 * kl_div(p, m) + 0.5 * kl_div(q, m)
    # JS divergence in base 2 is bounded in [0, 1]
    js_div = max(0.0, min(1.0, js_div))

    return {
        "js_divergence": round(js_div, 4),
        "wasserstein_distance": round(wasserstein, 4),
    }


@dataclass
class GateThresholds:
    min_assertion_score: float = 1.0
    min_rag_score: float = 0.80
    min_groundedness: float = 0.70
    min_pairwise_score: float = 0.0
    max_drift: float = 0.20
    max_score_drop: float = 0.05


@dataclass
class GateDecision:
    passed: bool
    status: str  # "PASSED" | "FAILED"
    deployment_action: str  # "PROCEED_CANARY_DEPLOYMENT" | "TRIGGER_ROLLBACK"
    failure_reasons: list[str] = field(default_factory=list)
    assertion_score: float = 0.0
    rag_score: float = 0.0
    pairwise_score: float = 0.0
    js_divergence: float = 0.0
    wasserstein_distance: float = 0.0
    score_drop: float = 0.0
    hallucination_count: int = 0
    assertion_summary: dict[str, Any] = field(default_factory=dict)
    rag_summary: dict[str, Any] = field(default_factory=dict)
    pairwise_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "deployment_action": self.deployment_action,
            "failure_reasons": self.failure_reasons,
            "metrics": {
                "assertion_score": round(self.assertion_score, 4),
                "rag_score": round(self.rag_score, 4),
                "pairwise_score": round(self.pairwise_score, 4),
                "js_divergence": round(self.js_divergence, 4),
                "wasserstein_distance": round(self.wasserstein_distance, 4),
                "score_drop": round(self.score_drop, 4),
                "hallucination_count": self.hallucination_count,
            },
            "assertions": self.assertion_summary,
            "rag": self.rag_summary,
            "pairwise": self.pairwise_summary,
        }


def load_dataset(source: Union[str, Path, list[dict[str, Any]], dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(source, list):
        return source
    if isinstance(source, dict):
        if "items" in source:
            return source["items"]
        if "samples" in source:
            return source["samples"]
        return [source]

    path = Path(source).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    text = path.read_text(encoding="utf-8-sig").strip()
    if text.startswith("["):
        return json.loads(text)
    elif text.startswith("{"):
        parsed = json.loads(text)
        if "items" in parsed:
            return parsed["items"]
        if "samples" in parsed:
            return parsed["samples"]
        return [parsed]
    else:
        # JSONL format
        lines = [json.loads(line) for line in text.splitlines() if line.strip()]
        return lines


class CIEvaluationGate:
    def __init__(self, thresholds: GateThresholds | None = None) -> None:
        self.thresholds = thresholds or GateThresholds()

    def evaluate(
        self,
        candidate_data: Union[str, Path, list[dict[str, Any]], dict[str, Any]],
        baseline_data: Union[str, Path, list[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> GateDecision:
        candidate_items = load_dataset(candidate_data)
        baseline_items = load_dataset(baseline_data) if baseline_data is not None else []
        baseline_map = {str(item.get("id")): item for item in baseline_items if "id" in item}

        failure_reasons: list[str] = []

        # 1. Deterministic Unit Assertions
        assertion_specs: list[dict[str, Any]] = []
        for item in candidate_items:
            out = item.get("response") or item.get("output") or item.get("content")
            # Direct assertions defined on item
            if "assertions" in item:
                for a in item["assertions"]:
                    if isinstance(a, dict):
                        a_copy = dict(a)
                        if "output" not in a_copy:
                            a_copy["output"] = out
                        assertion_specs.append(a_copy)
            # Item-level assertion shortcuts
            if "expected_output" in item:
                assertion_specs.append({
                    "name": f"{item.get('id', 'item')}_exact_match",
                    "type": "exact_match",
                    "output": out,
                    "expected": item["expected_output"],
                })
            if "regex_pattern" in item:
                assertion_specs.append({
                    "name": f"{item.get('id', 'item')}_regex",
                    "type": "regex",
                    "output": out,
                    "pattern": item["regex_pattern"],
                })
            if "json_schema" in item:
                assertion_specs.append({
                    "name": f"{item.get('id', 'item')}_json_schema",
                    "type": "json_schema",
                    "output": out,
                    "schema": item["json_schema"],
                })

        if assertion_specs:
            assertion_eval = evaluate_assertions(assertion_specs)
            assertion_score = assertion_eval.score
            assertion_summary = assertion_eval.to_dict()
            if assertion_score < self.thresholds.min_assertion_score:
                failure_reasons.append(
                    f"Assertion score {assertion_score:.3f} below required threshold {self.thresholds.min_assertion_score:.3f} "
                    f"({assertion_eval.failed}/{assertion_eval.total} failed)"
                )
        else:
            assertion_score = 1.0
            assertion_summary = {"total": 0, "passed": 0, "failed": 0, "score": 1.0}

        # 2. RAG Triad Evaluation
        rag_candidate_items = [
            it for it in candidate_items
            if (it.get("context") or it.get("retrieved_context") or it.get("chunks"))
        ]
        if rag_candidate_items:
            rag_eval = evaluate_rag_dataset(
                rag_candidate_items,
                hallucination_threshold=self.thresholds.min_groundedness,
            )
            rag_score = rag_eval.mean_score
            hallucinations = rag_eval.hallucination_count
            rag_summary = rag_eval.to_dict()

            if rag_score < self.thresholds.min_rag_score:
                failure_reasons.append(
                    f"RAG Triad score {rag_score:.3f} below required threshold {self.thresholds.min_rag_score:.3f}"
                )
            if hallucinations > 0:
                failure_reasons.append(
                    f"Detected {hallucinations} hallucinated response(s) with groundedness < {self.thresholds.min_groundedness:.2f}"
                )
        else:
            rag_score = 1.0
            hallucinations = 0
            rag_summary = {"count": 0, "mean_score": 1.0}

        # 3. Pairwise Evaluation vs Baseline
        pairwise_comparisons: list[dict[str, Any]] = []
        for item in candidate_items:
            item_id = str(item.get("id"))
            cand_resp = item.get("response") or item.get("output") or ""
            base_resp = item.get("baseline_response") or item.get("reference")
            if not base_resp and item_id in baseline_map:
                base_item = baseline_map[item_id]
                base_resp = base_item.get("response") or base_item.get("output") or base_item.get("reference")

            if base_resp:
                pairwise_comparisons.append({
                    "id": item_id,
                    "prompt": item.get("query") or item.get("prompt") or "",
                    "candidate": cand_resp,
                    "baseline": base_resp,
                    "optimal_length": item.get("optimal_length", 100),
                })

        if pairwise_comparisons:
            pairwise_eval = evaluate_pairwise(pairwise_comparisons)
            pairwise_score = pairwise_eval.pairwise_score
            pairwise_summary = pairwise_eval.to_dict()

            if pairwise_score < self.thresholds.min_pairwise_score:
                failure_reasons.append(
                    f"Pairwise comparison score {pairwise_score:.3f} below threshold {self.thresholds.min_pairwise_score:.3f} "
                    f"(losses: {pairwise_eval.losses}, wins: {pairwise_eval.wins})"
                )
        else:
            pairwise_score = 0.0
            pairwise_summary = {"total": 0, "pairwise_score": 0.0}

        # 4. Distribution Comparison & Semantic Drift vs Golden Baseline
        js_div = 0.0
        wass_dist = 0.0
        score_drop = 0.0

        if baseline_items and candidate_items:
            # Baseline RAG evaluation for distribution comparison
            rag_baseline_items = [
                it for it in baseline_items
                if (it.get("context") or it.get("retrieved_context") or it.get("chunks"))
            ]
            if rag_baseline_items and rag_candidate_items:
                base_rag_eval = evaluate_rag_dataset(rag_baseline_items)
                base_scores = [item.score for item in base_rag_eval.items]
                cand_scores = [item.score for item in rag_eval.items]
                dist_metrics = compute_distribution_metrics(base_scores, cand_scores)
                js_div = dist_metrics["js_divergence"]
                wass_dist = dist_metrics["wasserstein_distance"]

                score_drop = max(0.0, base_rag_eval.mean_score - rag_score)
                if score_drop > self.thresholds.max_score_drop:
                    failure_reasons.append(
                        f"RAG score regression drop {score_drop:.3f} exceeds tolerance {self.thresholds.max_score_drop:.3f} "
                        f"(baseline: {base_rag_eval.mean_score:.3f}, candidate: {rag_score:.3f})"
                    )

            # Compare token length distributions to catch runaway verbosity or truncation drift
            base_lens = [len(str(it.get("response") or it.get("output") or "").split()) for it in baseline_items]
            cand_lens = [len(str(it.get("response") or it.get("output") or "").split()) for it in candidate_items]
            len_dist = compute_distribution_metrics(base_lens, cand_lens)
            if js_div == 0.0:
                js_div = len_dist["js_divergence"]
                wass_dist = len_dist["wasserstein_distance"]

            if js_div > self.thresholds.max_drift:
                failure_reasons.append(
                    f"Semantic distribution drift (JS divergence {js_div:.3f}) exceeds threshold {self.thresholds.max_drift:.3f}"
                )

        passed = len(failure_reasons) == 0
        status = "PASSED" if passed else "FAILED"
        deployment_action = "PROCEED_CANARY_DEPLOYMENT" if passed else "TRIGGER_ROLLBACK"

        return GateDecision(
            passed=passed,
            status=status,
            deployment_action=deployment_action,
            failure_reasons=failure_reasons,
            assertion_score=assertion_score,
            rag_score=rag_score,
            pairwise_score=pairwise_score,
            js_divergence=js_div,
            wasserstein_distance=wass_dist,
            score_drop=score_drop,
            hallucination_count=hallucinations,
            assertion_summary=assertion_summary,
            rag_summary=rag_summary,
            pairwise_summary=pairwise_summary,
        )


def format_gate_report_human(decision: GateDecision) -> str:
    sep = "=" * 78
    subsep = "-" * 78

    status_tag = "[PASS: PROCEED_CANARY]" if decision.passed else "[FAIL: TRIGGER_ROLLBACK]"
    lines = [
        sep,
        "             TANKBENCH CI/CD AUTOMATED REGRESSION EVALUATION GATE",
        sep,
        f"Evaluation Status:     {decision.status} {status_tag}",
        f"Deployment Action:     {decision.deployment_action}",
        subsep,
        "[1] DETERMINISTIC UNIT ASSERTIONS",
        f"Pass Rate:             {decision.assertion_score * 100:.1f}%",
        f"Summary:               {decision.assertion_summary.get('passed', 0)} passed / {decision.assertion_summary.get('total', 0)} total",
        subsep,
        "[2] RAG TRIAD METRICS",
        f"Triad Composite Score: {decision.rag_score:.3f} / 1.0",
        f"Hallucination Flags:   {decision.hallucination_count} detected",
        subsep,
        "[3] CALIBRATED PAIRWISE EVALUATION",
        f"Pairwise Win/Tie Score:{decision.pairwise_score:+.3f}",
        f"Summary:               Wins: {decision.pairwise_summary.get('wins', 0)} | Losses: {decision.pairwise_summary.get('losses', 0)} | Ties: {decision.pairwise_summary.get('ties', 0)}",
        subsep,
        "[4] DISTRIBUTION DRIFT & REGRESSION",
        f"JS Divergence (Drift): {decision.js_divergence:.4f}",
        f"Wasserstein Distance:  {decision.wasserstein_distance:.4f}",
        f"Score Regression Drop: {decision.score_drop:.4f}",
        subsep,
    ]

    if decision.failure_reasons:
        lines.append("GATE VIOLATION DETAILS:")
        for r in decision.failure_reasons:
            lines.append(f"  [X] {r}")
        lines.append(sep)
    else:
        lines.append("ALL INVARIANTS SATISFIED: Zero regression detected. Safe to deploy.")
        lines.append(sep)

    return "\n".join(lines)


def run_ci_gate(
    candidate: Path,
    baseline: Path | None = None,
    thresholds: GateThresholds | None = None,
    as_json: bool = False,
    verbose: bool = False,
) -> int:
    """Run automated CI regression gate, print scorecard or JSON, return exit code 0 on pass or 1 on fail."""
    gate = CIEvaluationGate(thresholds=thresholds)
    decision = gate.evaluate(candidate_data=candidate, baseline_data=baseline)

    if as_json:
        print(json.dumps(decision.to_dict(), indent=2))
    else:
        print(format_gate_report_human(decision))

    return 0 if decision.passed else 1

