"""Structures shared by parsers and the chunker."""

from __future__ import annotations

from dataclasses import dataclass, field

type SourceLocation = dict[str, int | str]


@dataclass
class TableData:
    header: list[str]
    rows: list[list[str]]


@dataclass
class Block:
    kind: str
    text: str
    level: int | None
    section_path: list[str]
    loc: SourceLocation = field(default_factory=dict)
    fields: dict[str, str | None] | None = None
    table: TableData | None = None


@dataclass
class ParsedDocument:
    doc_type: str
    language_hint: str
    blocks: list[Block]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChunkConfig:
    target_tokens: int
    max_tokens: int
    overlap_tokens: int


@dataclass(frozen=True)
class ChunkDraft:
    ordinal: int
    text: str
    text_for_embedding: str
    section_path: tuple[str, ...]
    loc: SourceLocation
    requirement_ids: tuple[str, ...]
    token_count: int
