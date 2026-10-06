from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Union

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom",
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves"
}

INSTRUCTION_DIRECTIVES = {
    "summarize", "summary", "describe", "description", "explain", "explanation",
    "return", "format", "json", "markdown", "provide", "give", "find", "list",
    "state", "tell", "output", "show", "regarding", "question", "task", "customer",
    "user", "metadata", "profile", "please"
}


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"\b[A-Za-z0-9_'\-]+\b", text)]


def _stem(word: str) -> str:
    w = word.lower()
    for suff in ("ing", "tion", "ed", "es", "ly", "s"):
        if w.endswith(suff) and len(w) - len(suff) >= 3:
            return w[:-len(suff)]
    return w


def _content_words(text: str, filter_directives: bool = False) -> list[str]:
    tokens = _tokenize(text)
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    if filter_directives:
        filtered = [t for t in filtered if t not in INSTRUCTION_DIRECTIVES]
    return filtered


def _join_context(context: Union[str, list[str]]) -> str:
    if isinstance(context, list):
        return " \n ".join(context)
    return str(context)


def _token_matches(w: str, target_tokens: set[str], target_text: str) -> bool:
    w_low = w.lower()
    if w_low in target_tokens or w_low in target_text:
        return True
    w_stem = _stem(w_low)
    for t in target_tokens:
        if _stem(t) == w_stem or w_stem in t or t in w_stem:
            return True
    return False


def compute_context_relevance(
    query: str,
    context: Union[str, list[str]],
    *,
    custom_scorer: Callable[[str, Union[str, list[str]]], float] | None = None,
) -> float:
    """Measure the relevance of the retrieved context to the query.

    Returns a score between 0.0 and 1.0.
    """
    if custom_scorer is not None:
        return max(0.0, min(1.0, float(custom_scorer(query, context))))

    ctx_text = _join_context(context)
    if not ctx_text.strip():
        return 0.0

    ctx_tokens = set(_tokenize(ctx_text))
    # Extract query content words, prioritizing domain keywords over instruction directives
    q_words = _content_words(query, filter_directives=True)
    if not q_words:
        # Fall back to all content words if only directives exist
        q_words = _content_words(query, filter_directives=False)
    if not q_words:
        return 0.0

    matched = [w for w in q_words if _token_matches(w, ctx_tokens, ctx_text)]
    coverage = len(matched) / len(q_words)

    # Boost when core entities are completely covered
    if coverage >= 0.8:
        score = 1.0
    else:
        score = coverage

    return max(0.0, min(1.0, round(score, 4)))


def compute_groundedness(
    response: str,
    context: Union[str, list[str]],
    *,
    custom_scorer: Callable[[str, Union[str, list[str]]], float] | None = None,
) -> float:
    """Evaluate whether the response claims are grounded in the retrieved context.

    Returns a score between 0.0 and 1.0. Low score indicates hallucination.
    """
    if custom_scorer is not None:
        return max(0.0, min(1.0, float(custom_scorer(response, context))))

    resp_text = response.strip()
    if not resp_text:
        return 1.0

    ctx_text = _join_context(context).lower()
    if not ctx_text.strip():
        return 0.0

    ctx_tokens = set(_tokenize(ctx_text))

    # Detect if response is JSON
    is_json = False
    try:
        json_obj = json.loads(resp_text)
        is_json = True
    except Exception:
        is_json = False

    if is_json:
        # For structured data, evaluate data values and keys against context
        resp_tokens = _content_words(resp_text)
        if not resp_tokens:
            return 1.0
        # Common schema keys are permitted syntax
        schema_keys = {"true", "false", "null", "type", "id", "name", "user", "active", "status", "role"}
        informative = [t for t in resp_tokens if t not in schema_keys]
        if not informative:
            informative = resp_tokens
        matched = [w for w in informative if _token_matches(w, ctx_tokens, ctx_text)]
        ratio = len(matched) / len(informative)
        score = 1.0 if ratio >= 0.75 else (ratio / 0.75)
        return max(0.0, min(1.0, round(score, 4)))

    sentences = [s.strip() for s in re.split(r"[.\n!?]+", resp_text) if s.strip()]
    if not sentences:
        return 1.0

    sentence_scores: list[float] = []

    for sentence in sentences:
        c_words = _content_words(sentence)
        if not c_words:
            continue
        matched = [w for w in c_words if _token_matches(w, ctx_tokens, ctx_text)]
        word_ratio = len(matched) / len(c_words)

        # Content claims with >= 75% grounding are scored as fully grounded
        if word_ratio >= 0.75:
            s_score = 1.0
        else:
            s_score = word_ratio / 0.75

        sentence_scores.append(s_score)

    if not sentence_scores:
        return 1.0

    avg_score = sum(sentence_scores) / len(sentence_scores)
    return max(0.0, min(1.0, round(avg_score, 4)))


def compute_answer_relevance(
    query: str,
    response: str,
    *,
    custom_scorer: Callable[[str, str], float] | None = None,
) -> float:
    """Assess the relevance of the LLM response to the specific question or task.

    Returns a score between 0.0 and 1.0.
    """
    if custom_scorer is not None:
        return max(0.0, min(1.0, float(custom_scorer(query, response))))

    query_str = query.strip()
    resp_str = response.strip()

    if not resp_str or not query_str:
        return 0.0

    # Penalize evasive rejection
    evasion_patterns = [
        r"\bi cannot answer\b",
        r"\bi am unable to\b",
        r"\bi do not know\b",
        r"\bas an ai\b",
    ]
    if any(re.search(pat, resp_str.lower()) for pat in evasion_patterns):
        return 0.1

    resp_tokens = set(_tokenize(resp_str))

    # Check format request satisfaction (e.g. JSON requested and JSON produced)
    format_bonus = 0.0
    if "json" in query_str.lower():
        try:
            json.loads(resp_str)
            format_bonus = 0.2
        except Exception:
            pass

    q_words = _content_words(query_str, filter_directives=False)
    if not q_words:
        return 0.8

    matched = [w for w in q_words if _token_matches(w, resp_tokens, resp_str)]
    coverage = len(matched) / len(q_words)

    # Length sufficiency check
    length_ok = min(1.0, len(resp_tokens) / max(3, len(q_words)))

    score = (0.7 * coverage) + (0.3 * length_ok) + format_bonus
    return max(0.0, min(1.0, round(score, 4)))


@dataclass
class RAGTriadScore:
    context_relevance: float
    groundedness: float
    answer_relevance: float
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def score(self) -> float:
        """RAG Score = 1/3 * (CR + G + AR)"""
        raw = (1.0 / 3.0) * (self.context_relevance + self.groundedness + self.answer_relevance)
        return max(0.0, min(1.0, round(raw, 4)))

    def is_hallucination(self, threshold: float = 0.70) -> bool:
        return self.groundedness < threshold

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_relevance": self.context_relevance,
            "groundedness": self.groundedness,
            "answer_relevance": self.answer_relevance,
            "score": self.score,
            "hallucination": self.is_hallucination(),
            "details": self.details,
        }


@dataclass
class RAGBatchScore:
    count: int
    mean_context_relevance: float
    mean_groundedness: float
    mean_answer_relevance: float
    mean_score: float
    hallucination_count: int
    items: list[RAGTriadScore] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "mean_context_relevance": round(self.mean_context_relevance, 4),
            "mean_groundedness": round(self.mean_groundedness, 4),
            "mean_answer_relevance": round(self.mean_answer_relevance, 4),
            "mean_score": round(self.mean_score, 4),
            "hallucination_count": self.hallucination_count,
            "items": [item.to_dict() for item in self.items],
        }


def evaluate_rag_triad(
    query: str,
    context: Union[str, list[str]],
    response: str,
    *,
    custom_scorers: dict[str, Callable[..., float]] | None = None,
) -> RAGTriadScore:
    """Evaluate full RAG Triad: Context Relevance, Groundedness, Answer Relevance."""
    custom_scorers = custom_scorers or {}
    cr = compute_context_relevance(query, context, custom_scorer=custom_scorers.get("context_relevance"))
    g = compute_groundedness(response, context, custom_scorer=custom_scorers.get("groundedness"))
    ar = compute_answer_relevance(query, response, custom_scorer=custom_scorers.get("answer_relevance"))

    return RAGTriadScore(
        context_relevance=cr,
        groundedness=g,
        answer_relevance=ar,
        details={
            "query_length": len(query),
            "response_length": len(response),
            "context_chunks": len(context) if isinstance(context, list) else 1,
        },
    )


def evaluate_rag_dataset(
    samples: list[dict[str, Any]],
    *,
    custom_scorers: dict[str, Callable[..., float]] | None = None,
    hallucination_threshold: float = 0.70,
) -> RAGBatchScore:
    """Evaluate RAG Triad across a collection of samples."""
    if not samples:
        return RAGBatchScore(
            count=0,
            mean_context_relevance=0.0,
            mean_groundedness=0.0,
            mean_answer_relevance=0.0,
            mean_score=0.0,
            hallucination_count=0,
            items=[],
        )

    items: list[RAGTriadScore] = []
    cr_sum = 0.0
    g_sum = 0.0
    ar_sum = 0.0
    score_sum = 0.0
    hallucinations = 0

    for s in samples:
        query = str(s.get("query") or s.get("question") or s.get("prompt") or "")
        context = s.get("context") or s.get("retrieved_context") or s.get("chunks") or ""
        response = str(s.get("response") or s.get("answer") or s.get("output") or "")

        res = evaluate_rag_triad(query, context, response, custom_scorers=custom_scorers)
        items.append(res)
        cr_sum += res.context_relevance
        g_sum += res.groundedness
        ar_sum += res.answer_relevance
        score_sum += res.score
        if res.is_hallucination(threshold=hallucination_threshold):
            hallucinations += 1

    n = len(samples)
    return RAGBatchScore(
        count=n,
        mean_context_relevance=cr_sum / n,
        mean_groundedness=g_sum / n,
        mean_answer_relevance=ar_sum / n,
        mean_score=score_sum / n,
        hallucination_count=hallucinations,
        items=items,
    )
