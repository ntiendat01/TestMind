"""Group blocks by heading, then pack them to the token budget."""

from __future__ import annotations

import re
from dataclasses import replace

from app.core.interfaces import TokenCounter
from app.schemas.parsed import Block, ChunkConfig, ChunkDraft, ParsedDocument, TableData

_REQ = re.compile(r"REQ-\d+")


def chunk_document(
    parsed: ParsedDocument,
    doc_name: str,
    config: ChunkConfig,
    counter: TokenCounter,
) -> list[ChunkDraft]:
    drafts: list[ChunkDraft] = []
    ordinal = 0
    for group in _sections(parsed.blocks):
        for piece in _pack(group, config, counter):
            text = "\n".join(block.text for block in piece)
            path = tuple(piece[0].section_path)
            prefix = doc_name if not path else f"{doc_name} > {' > '.join(path)}"
            drafts.append(
                ChunkDraft(
                    ordinal=ordinal,
                    text=text,
                    text_for_embedding=f"{prefix}\n{text}",
                    section_path=path,
                    loc=dict(piece[0].loc),
                    requirement_ids=tuple(dict.fromkeys(_REQ.findall(text))),
                    token_count=sum(max(1, counter.count(block.text)) for block in piece),
                )
            )
            ordinal += 1
    return drafts


def _sections(blocks: list[Block]) -> list[list[Block]]:
    groups: list[list[Block]] = []
    current: list[Block] = []
    current_path: tuple[str, ...] | None = None
    for block in blocks:
        path = tuple(block.section_path)
        if current and path != current_path:
            groups.append(current)
            current = []
        current.append(block)
        current_path = path
    if current:
        groups.append(current)
    return groups


def _pack(blocks: list[Block], config: ChunkConfig, counter: TokenCounter) -> list[list[Block]]:
    packed: list[list[Block]] = []
    current: list[Block] = []
    tokens = 0

    def flush() -> None:
        nonlocal current, tokens
        if current:
            packed.append(current)
            current = []
            tokens = 0

    for block in blocks:
        count = max(1, counter.count(block.text))
        if block.table is not None:
            flush()
            packed.extend([piece] for piece in _pack_table(block, block.table, config, counter))
            continue
        if block.kind in {"row", "table"} or count > config.max_tokens:
            flush()
            packed.append([block])
            continue
        if current and tokens + count > config.target_tokens:
            overlap = _overlap(current, config.overlap_tokens, counter)
            flush()
            current = overlap
            tokens = sum(max(1, counter.count(item.text)) for item in current)
        current.append(block)
        tokens += count
    flush()
    return packed


def _pack_table(
    block: Block, table: TableData, config: ChunkConfig, counter: TokenCounter
) -> list[Block]:
    if not table.rows:
        return [block]
    parts: list[Block] = []
    rows: list[str] = []
    first = 2
    tokens = 0
    for number, cells in enumerate(table.rows, start=2):
        row = " | ".join(
            f"{label}: {value}" for label, value in zip(table.header, cells, strict=False) if value
        )
        if not row:
            continue
        count = max(1, counter.count(row))
        if rows and tokens + count > config.max_tokens:
            parts.append(_table_piece(block, rows, first))
            rows = []
            tokens = 0
        if not rows:
            first = number
        rows.append(row)
        tokens += count
    if rows:
        parts.append(_table_piece(block, rows, first))
    return parts or [block]


def _table_piece(block: Block, rows: list[str], first: int) -> Block:
    return replace(block, text="\n".join(rows), loc={**block.loc, "row": first}, table=None)


def _overlap(blocks: list[Block], overlap_tokens: int, counter: TokenCounter) -> list[Block]:
    chosen: list[Block] = []
    total = 0
    for block in reversed(blocks):
        count = max(1, counter.count(block.text))
        if count > overlap_tokens or total + count > overlap_tokens:
            break
        chosen.append(block)
        total += count
    chosen.reverse()
    return chosen
