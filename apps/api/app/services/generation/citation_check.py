"""Drop citations that were not in the retrieved context."""

from __future__ import annotations

import json

from app.schemas.records import CitationSource, ClaimOut, SearchHit
from pydantic import BaseModel, ValidationError


class ClaimIn(BaseModel):
    text: str
    chunk_ids: list[str]


class LLMAnswer(BaseModel):
    insufficient_evidence: bool = False
    answer: str = ""
    claims: list[ClaimIn] = []
    notes: str = ""


def parse_llm_json(raw: str) -> LLMAnswer:
    text = raw.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return LLMAnswer.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("invalid llm json") from exc


def check_citations(answer: LLMAnswer, hits: list[SearchHit]) -> list[ClaimOut]:
    by_id = {hit.chunk.id: hit for hit in hits}
    checked: list[ClaimOut] = []
    for claim in answer.claims:
        valid = [chunk_id for chunk_id in claim.chunk_ids if chunk_id in by_id]
        sources = [_source(by_id[chunk_id]) for chunk_id in valid]
        checked.append(
            ClaimOut(
                text=claim.text,
                chunk_ids=valid,
                status="verified" if valid else "unverified",
                sources=sources,
            )
        )
    return checked


def _source(hit: SearchHit) -> CitationSource:
    return CitationSource(
        chunk_id=hit.chunk.id,
        document_name=hit.chunk.document_name,
        section_path=list(hit.chunk.section_path),
        loc=dict(hit.chunk.loc),
    )
