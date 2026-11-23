"""Call the LLM and keep only citations that belong to the context."""

from __future__ import annotations

from app.core.errors import APIError
from app.core.interfaces import LLMClient
from app.schemas.records import QueryOutcome, SearchHit
from app.services.generation.citation_check import check_citations, parse_llm_json
from app.services.generation.prompt import render_user_prompt


def generate_answer(
    llm: LLMClient,
    *,
    system: str,
    prompt_version: str,
    question: str,
    hits: list[SearchHit],
) -> QueryOutcome:
    user = render_user_prompt(question, hits)
    last_error: Exception | None = None
    for attempt in range(2):
        extra = "" if attempt == 0 else "\nTrả về chỉ một JSON object hợp lệ."
        completion = llm.complete(system=system, user=user + extra)
        try:
            parsed = parse_llm_json(completion.content)
        except ValueError as exc:
            last_error = exc
            continue
        return QueryOutcome(
            insufficient_evidence=parsed.insufficient_evidence,
            answer="" if parsed.insufficient_evidence else parsed.answer,
            claims=[] if parsed.insufficient_evidence else check_citations(parsed, hits),
            notes=parsed.notes,
            hits=hits,
            prompt_version=prompt_version,
            tokens_in=completion.tokens_in,
            tokens_out=completion.tokens_out,
        )
    raise APIError(
        502,
        "llm_response_invalid",
        "The model did not return valid JSON.",
    ) from last_error
