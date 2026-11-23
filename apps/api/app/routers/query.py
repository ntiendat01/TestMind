"""Question answering as server-sent events."""

from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.container import Container
from app.routers.documents import get_container
from app.schemas.records import QueryOutcome
from app.services.generation.query import answer_query

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    doc_types: list[str] = Field(default_factory=list)
    module: str | None = None


@router.post("/v1/query")
def ask(body: QueryRequest, container: Container = Depends(get_container)) -> StreamingResponse:
    outcome = answer_query(
        question=body.query,
        doc_types=body.doc_types,
        module=body.module,
        store=container.store,
        embedder=container.embedder,
        llm=container.llm,
        counter=container.counter,
        system=container.prompt_text,
        prompt_version=container.prompt_version,
        limit=container.settings.retrieval_limit,
        token_budget=container.settings.context_token_budget,
        min_similarity=container.settings.retrieval_min_similarity,
    )
    return StreamingResponse(_events(outcome), media_type="text/event-stream")


def _events(outcome: QueryOutcome) -> Iterator[str]:
    retrieval = [
        {
            "chunk_id": hit.chunk.id,
            "score": hit.score,
            "section_path": list(hit.chunk.section_path),
            "loc": hit.chunk.loc,
            "document_name": hit.chunk.document_name,
            "text": hit.chunk.text,
        }
        for hit in outcome.hits
    ]
    final = {
        "insufficient_evidence": outcome.insufficient_evidence,
        "answer": outcome.answer,
        "claims": [
            {
                "text": claim.text,
                "chunk_ids": claim.chunk_ids,
                "status": claim.status,
                "sources": [
                    {
                        "chunk_id": source.chunk_id,
                        "document_name": source.document_name,
                        "section_path": source.section_path,
                        "loc": source.loc,
                    }
                    for source in claim.sources
                ],
            }
            for claim in outcome.claims
        ],
        "notes": outcome.notes,
    }
    usage = {
        "tokens_in": outcome.tokens_in,
        "tokens_out": outcome.tokens_out,
        "prompt_version": outcome.prompt_version,
        "latency_ms": outcome.latency_ms,
    }
    yield _event("retrieval", retrieval)
    yield _event("final", final)
    yield _event("usage", usage)


def _event(name: str, payload: object) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
