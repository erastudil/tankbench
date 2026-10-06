"""tankbench: harden a leaky patient. 0 offense is the point."""

__version__ = "0.2.0"

from tankbench.assertions import (
    AssertionResult,
    AssertionScore,
    AssertionSpec,
    AssertionType,
    assert_exact_match,
    assert_json_schema,
    assert_regex,
    evaluate_assertion,
    evaluate_assertions,
)
from tankbench.ci_gate import (
    CIEvaluationGate,
    GateDecision,
    GateThresholds,
    compute_distribution_metrics,
    run_ci_gate,
)
from tankbench.harness import grade, repo_root
from tankbench.idle_worker import (
    IdleComputeWorker,
    IdleWorkerConfig,
    IdleWorkResult,
    WorkCategory,
    run_worker_cli,
)
from tankbench.pairwise import (
    ComparisonResult,
    PairwiseComparison,
    PairwiseScore,
    compute_verbosity_penalty,
    evaluate_pairwise,
    evaluate_single_pairwise,
)
from tankbench.rag_triad import (
    RAGBatchScore,
    RAGTriadScore,
    compute_answer_relevance,
    compute_context_relevance,
    compute_groundedness,
    evaluate_rag_dataset,
    evaluate_rag_triad,
)
from tankbench.reset_blast import (
    BlastConfig,
    BlastResult,
    QuotaProvider,
    ResetDayBlastRunner,
    run_blast_cli,
)
from tankbench.scoring import Score, fold

__all__ = [
    "Score",
    "fold",
    "grade",
    "repo_root",
    "AssertionType",
    "AssertionResult",
    "AssertionScore",
    "AssertionSpec",
    "assert_exact_match",
    "assert_regex",
    "assert_json_schema",
    "evaluate_assertion",
    "evaluate_assertions",
    "RAGTriadScore",
    "RAGBatchScore",
    "compute_context_relevance",
    "compute_groundedness",
    "compute_answer_relevance",
    "evaluate_rag_triad",
    "evaluate_rag_dataset",
    "PairwiseComparison",
    "ComparisonResult",
    "PairwiseScore",
    "compute_verbosity_penalty",
    "evaluate_single_pairwise",
    "evaluate_pairwise",
    "GateThresholds",
    "GateDecision",
    "CIEvaluationGate",
    "compute_distribution_metrics",
    "run_ci_gate",
    "WorkCategory",
    "IdleWorkResult",
    "IdleWorkerConfig",
    "IdleComputeWorker",
    "run_worker_cli",
    "QuotaProvider",
    "BlastConfig",
    "BlastResult",
    "ResetDayBlastRunner",
    "run_blast_cli",
]
