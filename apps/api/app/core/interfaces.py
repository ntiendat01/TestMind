"""Swappable ports for eval and tests."""

from __future__ import annotations

from typing import Protocol

from app.schemas.parsed import ChunkDraft
from app.schemas.records import SearchHit, StoredVersion


class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...


class Embedder(Protocol):
    model_name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LLMResult(Protocol):
    content: str
    tokens_in: int
    tokens_out: int


class LLMClient(Protocol):
    def complete(self, *, system: str, user: str) -> LLMResult: ...


class DocumentStore(Protocol):
    def find_ready_by_hash(self, content_hash: str) -> StoredVersion | None: ...

    def save_ready(
        self,
        *,
        version_id: str,
        name: str,
        doc_type: str,
        module: str | None,
        content_hash: str,
        chunks: list[tuple[ChunkDraft, str, list[float]]],
        embedding_model: str,
    ) -> StoredVersion: ...

    def mark_failed(
        self,
        *,
        version_id: str,
        name: str,
        doc_type: str,
        module: str | None,
        content_hash: str,
        error: str,
    ) -> StoredVersion: ...

    def get_version(self, version_id: str) -> StoredVersion | None: ...

    def search_dense(
        self,
        vector: list[float],
        limit: int,
        doc_types: list[str] | None,
        module: str | None,
    ) -> list[SearchHit]: ...

    def save_query(
        self,
        *,
        text: str,
        filters: dict[str, object],
        retrieved: list[dict[str, object]],
        answer: str,
        insufficient_evidence: bool,
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        prompt_version: str,
    ) -> None: ...
