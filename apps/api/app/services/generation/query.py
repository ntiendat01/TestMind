"""Answer a question from active chunks, or refuse when none match."""

from __future__ import annotations

import time

from app.core.interfaces import DocumentStore, Embedder, LLMClient, TokenCounter
from app.schemas.records import QueryOutcome, SearchHit
from app.services.generation.answer import generate_answer
from app.services.retrieval.pipeline import retrieve_dense


def answer_query(
    *,
    question: str,
    doc_types: list[str],
    module: str | None,
    store: DocumentStore,
    embedder: Embedder,
    llm: LLMClient,
    counter: TokenCounter,
    system: str,
    prompt_version: str,
    limit: int,
    token_budget: int,
) -> QueryOutcome:
    started = time.perf_counter()
    hits = retrieve_dense(
        question=question,
        embedder=embedder,
        store=store,
        counter=counter,
        doc_types=doc_types,
        module=module,
        limit=limit,
        token_budget=token_budget,
    )
    if not hits:
        outcome = _refuse(prompt_version)
    else:
        outcome = generate_answer(
            llm,
            system=system,
            prompt_version=prompt_version,
            question=question,
            hits=hits,
        )
    elapsed = int((time.perf_counter() - started) * 1000)
    store.save_query(
        text=question,
        filters={"doc_types": doc_types, "module": module},
        retrieved=[_retrieved(hit) for hit in outcome.hits],
        answer=outcome.answer,
        insufficient_evidence=outcome.insufficient_evidence,
        tokens_in=outcome.tokens_in,
        tokens_out=outcome.tokens_out,
        latency_ms=elapsed,
        prompt_version=outcome.prompt_version,
    )
    return outcome


def _refuse(prompt_version: str) -> QueryOutcome:
    return QueryOutcome(
        insufficient_evidence=True,
        answer="",
        claims=[],
        notes="No active chunk was retrieved.",
        hits=[],
        prompt_version=prompt_version,
        tokens_in=0,
        tokens_out=0,
    )


def _retrieved(hit: SearchHit) -> dict[str, object]:
    return {
        "chunk_id": hit.chunk.id,
        "score": hit.score,
        "section_path": list(hit.chunk.section_path),
    }
