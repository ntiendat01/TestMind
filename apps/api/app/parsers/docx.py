"""Read the document body in order and use block order as the source location."""

import re
from io import BytesIO
from zipfile import BadZipFile

from app.schemas.parsed import Block, ParsedDocument, TableData
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml.etree import XMLSyntaxError  # type: ignore[import-untyped]

_HEADING = re.compile(r"Heading([1-9])")


def parse_docx(data: bytes, doc_type: str) -> ParsedDocument:
    try:
        blocks = _body_blocks(data)
    except (BadZipFile, PackageNotFoundError, KeyError, OSError, XMLSyntaxError, ValueError) as exc:
        raise ValueError("The document could not be read as DOCX.") from exc
    return ParsedDocument(doc_type, "vi", blocks)


def _body_blocks(data: bytes) -> list[Block]:
    document = Document(BytesIO(data))
    blocks: list[Block] = []
    headings: list[tuple[int, str]] = []
    for index, item in enumerate(document.iter_inner_content()):
        if isinstance(item, Paragraph):
            text = item.text.strip()
            if not text:
                continue
            style = item.style
            heading = _HEADING.fullmatch(style.style_id or "") if style is not None else None
            level = int(heading[1]) if heading else None
            if level is not None:
                while headings and headings[-1][0] >= level:
                    headings.pop()
                headings.append((level, text))
            path = [title for _, title in headings]
            kind = "heading" if level is not None else "paragraph"
            blocks.append(Block(kind, text, level, path, {"paragraph_idx": index}))
        else:
            if block := _table_block(item, index, [title for _, title in headings]):
                blocks.append(block)
    return blocks


def _table_block(table: Table, index: int, path: list[str]) -> Block | None:
    rows = [
        [""] * row.grid_cols_before
        + [cell.text.strip() for cell in row.cells]
        + [""] * row.grid_cols_after
        for row in table.rows
    ]
    if not rows or not any(any(row) for row in rows):
        return None
    width = max(map(len, rows))
    header = rows[0] + [""] * (width - len(rows[0]))
    names = [name or f"Column {col}" for col, name in enumerate(header, start=1)]
    return Block(
        "table",
        " | ".join(names),
        None,
        path,
        {"paragraph_idx": index},
        table=TableData(names, rows[1:]),
    )
