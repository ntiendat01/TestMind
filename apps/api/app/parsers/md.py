"""Markdown and plain-text parser. Rust port is M3."""

from __future__ import annotations

import re

from app.schemas.parsed import Block, ParsedDocument

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def parse_text(text: str, doc_type: str, *, markdown: bool) -> ParsedDocument:
    cleaned = text.replace("\r\n", "\n").replace("\x00", "")
    blocks = _markdown_blocks(cleaned) if markdown else _plain_blocks(cleaned)
    return ParsedDocument(doc_type=doc_type, language_hint="vi", blocks=blocks)


def _plain_blocks(text: str) -> list[Block]:
    body = text.strip()
    if not body:
        return []
    return [
        Block(
            kind="paragraph",
            text=body,
            level=None,
            section_path=[],
            loc={"paragraph_idx": 0},
        )
    ]


def _markdown_blocks(text: str) -> list[Block]:
    blocks: list[Block] = []
    stack: list[tuple[int, str]] = []
    buffer: list[str] = []

    def path() -> list[str]:
        return [title for _, title in stack]

    def flush() -> None:
        nonlocal buffer
        lines = buffer
        buffer = []
        nonempty = [line for line in lines if line.strip()]
        if not nonempty:
            return
        body = "\n".join(nonempty)
        kind = "table" if all(line.strip().startswith("|") for line in nonempty) else "paragraph"
        blocks.append(Block(kind=kind, text=body, level=None, section_path=path(), loc={}))

    for line in text.split("\n"):
        match = _HEADING.match(line)
        if match is None:
            buffer.append(line)
            continue
        flush()
        level = len(match.group(1))
        title = match.group(2).strip()
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        blocks.append(Block(kind="heading", text=title, level=level, section_path=path(), loc={}))
    flush()
    for index, block in enumerate(blocks):
        block.loc = {"paragraph_idx": index}
    return blocks
