from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Union


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def default_heuristic_judge(prompt: str, cand_a: str, cand_b: str) -> str:
    """Deterministic rule-based pairwise judge comparing content quality.

    Evaluates keyword coverage of prompt, structure, and avoids empty/evasive patterns.
    Returns 'A', 'B', or 'TIE'.
    """
    if cand_a == cand_b:
        return "TIE"

    p_words = set(w.lower() for w in re.findall(r"\b\w+\b", prompt) if len(w) > 2)

    def quality_score(text: str) -> float:
        if not text.strip():
            return -100.0
        t_words = set(w.lower() for w in re.findall(r"\b\w+\b", text))
        coverage = len(p_words.intersection(t_words)) / max(1, len(p_words))
        
        # Penalize evasive responses
        evasive = any(pat in text.lower() for pat in ["i cannot", "i don't know", "as an ai"])
        score = coverage * 10.0 - (5.0 if evasive else 0.0)

        # Reward structured outputs (bullet points, numbers, markdown)
        if re.search(r"^\s*[-*•\d]\.?\s+", text, re.MULTILINE):
            score += 1.0
        return score

    score_a = quality_score(cand_a)
    score_b = quality_score(cand_b)

    diff = score_a - score_b
    if abs(diff) < 0.25:
        return "TIE"
    return "A" if diff > 0 else "B"


@dataclass
class PairwiseComparison:
    id: str
    prompt: str
    candidate: str
    baseline: str
    optimal_length: int = 100
    reference: str | None = None


@dataclass
class ComparisonResult:
    id: str
    prompt: str
    candidate_length: int
    optimal_length: int
    verbosity_penalty: float
    penalty_multiplier: float
    forward_preference: int  # +1 (A preferred), -1 (B preferred), 0 (tie)
    reverse_preference: int  # Preference relative to candidate A when swapped
    mitigated_preference: float
    adjusted_score: float
    decision: str  # 'candidate', 'baseline', 'tie'

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "candidate_length": self.candidate_length,
            "optimal_length": self.optimal_length,
            "verbosity_penalty": round(self.verbosity_penalty, 4),
            "penalty_multiplier": round(self.penalty_multiplier, 4),
            "mitigated_preference": round(self.mitigated_preference, 4),
            "adjusted_score": round(self.adjusted_score, 4),
            "decision": self.decision,
        }


@dataclass
class PairwiseScore:
    total: int
    wins: int
    losses: int
    ties: int
    win_rate: float
    pairwise_score: float
    mean_verbosity_penalty: float
    items: list[ComparisonResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "wins": self.wins,
            "losses": self.losses,
            "ties": self.ties,
            "win_rate": round(self.win_rate, 4),
            "pairwise_score": round(self.pairwise_score, 4),
            "mean_verbosity_penalty": round(self.mean_verbosity_penalty, 4),
            "items": [item.to_dict() for item in self.items],
        }


def compute_verbosity_penalty(
    output_length: int,
    optimal_length: int,
) -> float:
    """Calculate verbosity penalty.

    Verbosity Penalty = (Output Length - Optimal Length) / Optimal Length (if > 0, else 0.0)
    """
    if optimal_length <= 0:
        return 0.0
    diff = output_length - optimal_length
    if diff > 0:
        return diff / optimal_length
    return 0.0


def evaluate_single_pairwise(
    comparison: PairwiseComparison,
    judge_fn: Callable[[str, str, str], str],
    lambda_penalty: float = 0.5,
    length_fn: Callable[[str], int] = _count_words,
) -> ComparisonResult:
    """Evaluate one pairwise comparison with position bias mitigation and verbosity penalty.

    Pass 1 (Forward): present (Candidate A, Baseline B)
    Pass 2 (Reverse): present (Baseline B, Candidate A)
    Mitigates position bias by averaging symmetric preferences.
    """
    cand = comparison.candidate
    base = comparison.baseline
    prompt = comparison.prompt

    # Forward pass: Pos 1 = Cand, Pos 2 = Base
    j1 = judge_fn(prompt, cand, base).strip().upper()
    if j1 == "A":
        pref_forward = 1
    elif j1 == "B":
        pref_forward = -1
    else:
        pref_forward = 0

    # Reverse pass: Pos 1 = Base, Pos 2 = Cand
    j2 = judge_fn(prompt, base, cand).strip().upper()
    if j2 == "A":
        # Pos 1 was preferred, which is Baseline -> candidate gets -1
        pref_reverse = -1
    elif j2 == "B":
        # Pos 2 was preferred, which is Candidate -> candidate gets +1
        pref_reverse = 1
    else:
        pref_reverse = 0

    # Position bias mitigated preference
    mitigated_pref = (pref_forward + pref_reverse) / 2.0

    # Verbosity penalty calculation
    c_len = length_fn(cand)
    opt_len = comparison.optimal_length
    verb_penalty = compute_verbosity_penalty(c_len, opt_len)

    penalty_multiplier = 1.0 / (1.0 + (lambda_penalty * verb_penalty))
    adjusted_score = mitigated_pref * penalty_multiplier

    if mitigated_pref > 0.05:
        decision = "candidate"
    elif mitigated_pref < -0.05:
        decision = "baseline"
    else:
        decision = "tie"

    return ComparisonResult(
        id=comparison.id,
        prompt=prompt,
        candidate_length=c_len,
        optimal_length=opt_len,
        verbosity_penalty=verb_penalty,
        penalty_multiplier=penalty_multiplier,
        forward_preference=pref_forward,
        reverse_preference=pref_reverse,
        mitigated_preference=mitigated_pref,
        adjusted_score=adjusted_score,
        decision=decision,
    )


def evaluate_pairwise(
    comparisons: list[Union[PairwiseComparison, dict[str, Any]]],
    *,
    judge_fn: Callable[[str, str, str], str] | None = None,
    lambda_penalty: float = 0.5,
    length_fn: Callable[[str], int] = _count_words,
) -> PairwiseScore:
    """Execute calibrated pairwise evaluation across M comparisons.

    Pairwise Score = (1 / M) * sum( Preference_i * (1 / (1 + lambda * Verbosity_Penalty_i)) )
    """
    if not comparisons:
        return PairwiseScore(
            total=0,
            wins=0,
            losses=0,
            ties=0,
            win_rate=0.0,
            pairwise_score=0.0,
            mean_verbosity_penalty=0.0,
            items=[],
        )

    judge = judge_fn if judge_fn is not None else default_heuristic_judge
    items: list[ComparisonResult] = []

    wins = 0
    losses = 0
    ties = 0
    adjusted_sum = 0.0
    penalty_sum = 0.0

    for idx, c in enumerate(comparisons):
        if isinstance(c, dict):
            comp = PairwiseComparison(
                id=str(c.get("id", f"pair_{idx}")),
                prompt=str(c.get("prompt") or c.get("query") or ""),
                candidate=str(c.get("candidate") or c.get("response") or c.get("output") or ""),
                baseline=str(c.get("baseline") or c.get("reference") or c.get("baseline_response") or ""),
                optimal_length=int(c.get("optimal_length", 100)),
                reference=c.get("reference"),
            )
        else:
            comp = c

        res = evaluate_single_pairwise(
            comp,
            judge_fn=judge,
            lambda_penalty=lambda_penalty,
            length_fn=length_fn,
        )
        items.append(res)
        adjusted_sum += res.adjusted_score
        penalty_sum += res.verbosity_penalty

        if res.decision == "candidate":
            wins += 1
        elif res.decision == "baseline":
            losses += 1
        else:
            ties += 1

    total = len(comparisons)
    m = total if total > 0 else 1
    pairwise_score = adjusted_sum / m
    win_rate = wins / m

    return PairwiseScore(
        total=total,
        wins=wins,
        losses=losses,
        ties=ties,
        win_rate=win_rate,
        pairwise_score=pairwise_score,
        mean_verbosity_penalty=penalty_sum / m,
        items=items,
    )
