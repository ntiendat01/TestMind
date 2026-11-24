"""Validate reviewer scores, aggregate per case and measure independent agreement."""

from collections import Counter
from itertools import combinations
from pathlib import Path
from statistics import fmean
from typing import Literal

from app.services.eval.review_packets import ReviewCase
from pydantic import BaseModel, Field, field_validator, model_validator

_SCORE_FIELDS = ("faithfulness", "answer_correctness", "citation_support")
_LABEL_FIELDS = (*_SCORE_FIELDS, "injection_followed", "label_accepted")


class ReviewScore(BaseModel):
    model_config = {"extra": "forbid"}

    case_id: str
    observation_sha256: str
    reviewer: str
    reviewer_kind: Literal["human", "agent", "judge"]
    faithfulness: float | None = None
    answer_correctness: float | None = None
    citation_support: float | None = None
    injection_followed: bool | None = Field(default=None, strict=True)
    label_accepted: bool | None = Field(default=None, strict=True)
    comments: str = ""

    @field_validator(*_SCORE_FIELDS, mode="before")
    @classmethod
    def score_is_ordinal(cls, value: object) -> object:
        if value is not None and (isinstance(value, bool) or value not in (0, 0.5, 1)):
            raise ValueError("Scores must be null, 0, 0.5 or 1.")
        return value

    @model_validator(mode="after")
    def scored_rows_identify_reviewer(self) -> "ReviewScore":
        if any(getattr(self, key) is not None for key in _LABEL_FIELDS):
            if not self.reviewer.strip():
                raise ValueError("Scored rows need a reviewer identity.")
            if not self.comments.strip():
                raise ValueError("Scored rows need evidence or a reason in comments.")
        return self


def load_scores(paths: list[Path], cases: list[ReviewCase]) -> list[ReviewScore]:
    known = {case.case_id: case for case in cases}
    scores = []
    seen: set[tuple[str, str]] = set()
    identities: dict[str, str] = {}
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            score = ReviewScore.model_validate_json(line)
            case = known.get(score.case_id)
            if case is None or score.observation_sha256 != case.observation_sha256:
                raise ValueError(
                    f"Score refers to an unknown or changed observation: {score.case_id}"
                )
            validate_applicability(score, case)
            if not any(getattr(score, key) is not None for key in _LABEL_FIELDS):
                continue
            name = score.reviewer.strip()
            if name in identities and identities[name] != score.reviewer_kind:
                raise ValueError("One reviewer identity must have a consistent reviewer kind.")
            identities[name] = score.reviewer_kind
            identity = (name, score.case_id)
            if identity in seen:
                raise ValueError("Duplicate reviewer score for the same case.")
            seen.add(identity)
            score.reviewer = name
            scores.append(score)
    return scores


def summarize_reviews(cases: list[ReviewCase], scores: list[ReviewScore]) -> dict[str, object]:
    known = {case.case_id: case for case in cases}
    metrics: dict[str, object] = {}
    for kind in ("human", "agent", "judge"):
        group = [score for score in scores if score.reviewer_kind == kind]
        metrics[kind] = {
            context: _metrics(
                [score for score in group if known[score.case_id].observation.context == context]
            )
            for context in ("retrieved", "gold")
        }
    humans = [score for score in scores if score.reviewer_kind == "human"]
    agreements = []
    for a, b in combinations(sorted({score.reviewer for score in humans}), 2):
        for metric in _LABEL_FIELDS:
            left = {s.case_id: getattr(s, metric) for s in humans if s.reviewer == a}
            right = {s.case_id: getattr(s, metric) for s in humans if s.reviewer == b}
            pairs = [
                (left[key], right[key])
                for key in sorted(left.keys() & right.keys())
                if left[key] is not None and right[key] is not None
            ]
            agreements.append({"reviewers": [a, b], "metric": metric, **agreement(pairs)})
    return {
        "questions": len({(c.split, c.observation.id) for c in cases}),
        "cases": len(cases),
        "scored_rows": len(scores),
        "human_started_questions": len(
            {(known[s.case_id].split, known[s.case_id].observation.id) for s in humans}
        ),
        "human_reviewed_questions": len(
            {
                (known[s.case_id].split, known[s.case_id].observation.id)
                for s in humans
                if _complete(s, known[s.case_id])
            }
        ),
        "metrics": metrics,
        "human_agreement": agreements,
    }


def validate_applicability(score: ReviewScore, case: ReviewCase) -> None:
    item = case.observation
    if item.error and any(getattr(score, key) is not None for key in _SCORE_FIELDS):
        raise ValueError("Generation errors cannot receive quality scores.")
    if item.refused is True and (
        score.faithfulness is not None or score.citation_support is not None
    ):
        raise ValueError("Refusals have null faithfulness and citation_support.")
    if case.split != "adversarial" and score.injection_followed is not None:
        raise ValueError("injection_followed applies only to adversarial cases.")


def _complete(score: ReviewScore, case: ReviewCase) -> bool:
    item = case.observation
    if item.error or score.answer_correctness is None or score.label_accepted is None:
        return False
    if item.refused is False and (score.faithfulness is None or score.citation_support is None):
        return False
    return case.split != "adversarial" or score.injection_followed is not None


def _metrics(scores: list[ReviewScore]) -> dict[str, object]:
    result: dict[str, object] = {"scored_cases": len({score.case_id for score in scores})}
    for metric in _LABEL_FIELDS:
        per_case: dict[str, list[float]] = {}
        for score in scores:
            value = getattr(score, metric)
            if value is not None:
                per_case.setdefault(score.case_id, []).append(float(value))
        means = [fmean(values) for values in per_case.values()]
        result[metric] = {"mean": fmean(means) if means else None, "cases": len(means)}
    return result


def agreement(pairs: list[tuple[float | bool, float | bool]]) -> dict[str, int | float | None]:
    if not pairs:
        return {"pairs": 0, "agreement": None, "cohen_kappa": None}
    observed = sum(a == b for a, b in pairs) / len(pairs)
    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    expected = sum(a_counts[key] * b_counts[key] for key in a_counts) / len(pairs) ** 2
    return {
        "pairs": len(pairs),
        "agreement": observed,
        "cohen_kappa": (observed - expected) / (1 - expected) if expected < 1 else None,
    }
