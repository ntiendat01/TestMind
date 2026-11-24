"""Retrieval metrics and a refusal-threshold sweep on labeled dev queries."""

from dataclasses import dataclass
from math import log2, nextafter
from statistics import fmean


@dataclass(frozen=True)
class Observation:
    id: str
    kind: str
    answerable: bool
    gold: frozenset[str]
    retrieved: tuple[str, ...]
    top_score: float | None
    latency_ms: float
    question: str = ""
    expected_points: tuple[str, ...] = ()
    sources: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class Threshold:
    minimum: float
    false_answers: int
    over_refusals: int


def recall_at(items: list[Observation], k: int) -> float | None:
    return _mean(
        [
            len(item.gold.intersection(item.retrieved[:k])) / len(item.gold)
            for item in items
            if item.answerable
        ]
    )


def reciprocal_rank(item: Observation) -> float:
    return next(
        (1 / rank for rank, hit in enumerate(item.retrieved, start=1) if hit in item.gold),
        0.0,
    )


def mrr(items: list[Observation]) -> float | None:
    return _mean([reciprocal_rank(item) for item in items if item.answerable])


def precision_at(items: list[Observation], k: int) -> float | None:
    return _mean(
        [len(item.gold.intersection(item.retrieved[:k])) / k for item in items if item.answerable]
    )


def ndcg_at(items: list[Observation], k: int) -> float | None:
    scores = []
    for item in items:
        if not item.answerable:
            continue
        seen: set[str] = set()
        dcg = 0.0
        for rank, hit in enumerate(item.retrieved[:k], start=1):
            if hit in item.gold and hit not in seen:
                dcg += 1 / log2(rank + 1)
            seen.add(hit)
        ideal = sum(1 / log2(rank + 1) for rank in range(1, min(k, len(item.gold)) + 1))
        scores.append(dcg / ideal)
    return _mean(scores)


def refusal_rates(items: list[Observation], threshold: Threshold) -> dict[str, float | None]:
    answerable = sum(item.answerable for item in items)
    unanswerable = len(items) - answerable
    return {
        "refusal_correct": 1 - threshold.false_answers / unanswerable if unanswerable else None,
        "false_accept_rate": threshold.false_answers / unanswerable if unanswerable else None,
        "over_refusal": threshold.over_refusals / answerable if answerable else None,
    }


def _mean(values: list[float]) -> float | None:
    return fmean(values) if values else None


def sweep_thresholds(items: list[Observation]) -> list[Threshold]:
    scores = {item.top_score for item in items if item.top_score is not None}
    thresholds = sorted({-1.0, 1.0, *(nextafter(score, 1.0) for score in scores)})
    return [evaluate_threshold(items, threshold) for threshold in thresholds]


def evaluate_threshold(items: list[Observation], minimum: float) -> Threshold:
    false_answers = 0
    over_refusals = 0
    for item in items:
        passed = item.top_score is not None and item.top_score >= minimum
        false_answers += int(passed and not item.answerable)
        over_refusals += int(not passed and item.answerable)
    return Threshold(minimum, false_answers, over_refusals)


def best_threshold(items: list[Observation]) -> Threshold:
    return min(
        sweep_thresholds(items),
        key=lambda item: (
            item.false_answers + item.over_refusals,
            item.false_answers,
            item.minimum,
        ),
    )
