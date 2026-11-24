"""Measure generation and raw citation membership through the production generator."""

from dataclasses import asdict, dataclass, field
from time import perf_counter

import httpx
from app.core.errors import APIError
from app.core.interfaces import LLMClient, LLMResult
from app.schemas.records import SearchHit
from app.services.eval.runner import EvalQuestion
from app.services.generation.answer import generate_answer
from app.services.generation.citation_check import parse_llm_json


@dataclass
class AuditedLLM:
    client: LLMClient
    tokens_in: int = 0
    tokens_out: int = 0
    responses: list[str] = field(default_factory=list)

    def complete(self, *, system: str, user: str) -> LLMResult:
        result = self.client.complete(system=system, user=user)
        self.tokens_in += result.tokens_in
        self.tokens_out += result.tokens_out
        self.responses.append(result.content)
        return result


@dataclass
class GenerationObservation:
    id: str
    context: str
    question: str
    answerable: bool
    expected_points: list[str]
    sources: list[dict[str, object]]
    error: str | None = None
    refused: bool | None = None
    answer: str = ""
    notes: str = ""
    claims: list[dict[str, object]] = field(default_factory=list)
    raw_claims: list[dict[str, object]] = field(default_factory=list)
    citations_total: int = 0
    citations_valid: int = 0
    claims_total: int = 0
    claims_cited: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0
    kind: str = ""


def evaluate_answer(
    question: EvalQuestion,
    variant: str,
    hits: list[SearchHit],
    llm: LLMClient,
    *,
    system: str,
    prompt_version: str,
) -> GenerationObservation:
    audited = AuditedLLM(llm)
    item = GenerationObservation(
        question.id,
        variant,
        question.question,
        question.answerable,
        question.gold_answer_points,
        [
            {
                "chunk_id": hit.chunk.id,
                "document": hit.chunk.document_name,
                "section_path": list(hit.chunk.section_path),
                "loc": hit.chunk.loc,
                "text": hit.chunk.text,
            }
            for hit in hits
        ],
    )
    started = perf_counter()
    item.kind = question.type
    try:
        outcome = generate_answer(
            audited,
            system=system,
            prompt_version=prompt_version,
            question=question.question,
            hits=hits,
        )
        raw = parse_llm_json(audited.responses[-1])
        item.raw_claims = [claim.model_dump() for claim in raw.claims]
        valid_ids = {hit.chunk.id for hit in hits}
        references = [ref for claim in raw.claims for ref in claim.chunk_ids]
        item.citations_total = len(references)
        item.citations_valid = sum(ref in valid_ids for ref in references)
        item.claims_total = len(raw.claims)
        item.claims_cited = sum(
            any(ref in valid_ids for ref in claim.chunk_ids) for claim in raw.claims
        )
        item.refused = outcome.insufficient_evidence
        item.answer = outcome.answer
        item.notes = outcome.notes
        item.claims = [asdict(claim) for claim in outcome.claims]
    except APIError as exc:
        item.error = exc.code
    except httpx.TransportError:
        item.error = "llm_transport_error"
    except (ValueError, KeyError, IndexError, TypeError):
        item.error = "llm_response_invalid"
    item.tokens_in = audited.tokens_in
    item.tokens_out = audited.tokens_out
    item.latency_ms = (perf_counter() - started) * 1000
    return item


def generation_metrics(items: list[GenerationObservation]) -> dict[str, float | int | None]:
    completed = [item for item in items if item.error is None]
    answerable = [item for item in completed if item.answerable]
    unanswerable = [item for item in completed if not item.answerable]
    answered = [item for item in completed if item.refused is False]
    total_refs = sum(item.citations_total for item in completed)
    return {
        "samples": len(items),
        "completed": len(completed),
        "errors": len(items) - len(completed),
        "refusal_correct": _ratio(
            sum(item.refused is True for item in unanswerable), len(unanswerable)
        ),
        "false_answer_rate": _ratio(
            sum(item.refused is False for item in unanswerable), len(unanswerable)
        ),
        "over_refusal": _ratio(sum(item.refused is True for item in answerable), len(answerable)),
        "citation_validity": _ratio(sum(item.citations_valid for item in completed), total_refs),
        "answer_citation_coverage": _ratio(
            sum(
                item.claims_total > 0 and item.claims_total == item.claims_cited
                for item in answered
            ),
            len(answered),
        ),
        "tokens_in": sum(item.tokens_in for item in items),
        "tokens_out": sum(item.tokens_out for item in items),
        "faithfulness": None,
        "answer_correctness": None,
        "citation_support": None,
        "cost": None,
    }


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None
