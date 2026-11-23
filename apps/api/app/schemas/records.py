"""Records passed between the store, retrieval, and generation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StoredChunk:
    id: str
    version_id: str
    ordinal: int
    text: str
    section_path: tuple[str, ...]
    loc: dict[str, int]
    requirement_ids: tuple[str, ...]
    token_count: int
    is_active: bool
    doc_type: str
    module: str | None
    document_name: str


@dataclass
class StoredVersion:
    id: str
    document_id: str
    document_name: str
    doc_type: str
    module: str | None
    version: int
    content_hash: str
    is_active: bool
    status: str
    error: str | None
    progress: int
    chunk_count: int


@dataclass
class SearchHit:
    chunk: StoredChunk
    score: float


@dataclass
class CitationSource:
    chunk_id: str
    document_name: str
    section_path: list[str]
    loc: dict[str, int]


@dataclass
class ClaimOut:
    text: str
    chunk_ids: list[str]
    status: str
    sources: list[CitationSource] = field(default_factory=list)


@dataclass
class DocumentSummary:
    document_id: str
    name: str
    doc_type: str
    module: str | None
    version_id: str
    version: int
    status: str
    chunk_count: int
    error: str | None


@dataclass
class QueryOutcome:
    insufficient_evidence: bool
    answer: str
    claims: list[ClaimOut]
    notes: str
    hits: list[SearchHit]
    prompt_version: str
    tokens_in: int
    tokens_out: int
    latency_ms: int = 0
