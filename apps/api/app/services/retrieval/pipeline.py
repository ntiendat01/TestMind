"""Dense retrieval. Lexical search and rerank arrive in M3."""

from __future__ import annotations

from app.core.interfaces import DocumentStore, Embedder, TokenCounter
from app.schemas.records import SearchHit


def retrieve_dense(
    *,
    question: str,
    embedder: Embedder,
    store: DocumentStore,
    counter: TokenCounter,
    doc_types: list[str] | None,
    module: str | None,
    limit: int,
    token_budget: int,
) -> list[SearchHit]:
    from app.services.retrieval.context import build_context

    vector = embedder.embed([question])[0]
    hits = store.search_dense(vector, limit, doc_types or None, module)
    return build_context(hits, token_budget, counter)
