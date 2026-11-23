"""Structures shared by parsers and the chunker."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Block:
    kind: str
    text: str
    level: int | None
    section_path: list[str]
    loc: dict[str, int] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    doc_type: str
    language_hint: str
    blocks: list[Block]


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
    loc: dict[str, int]
    requirement_ids: tuple[str, ...]
    token_count: int
