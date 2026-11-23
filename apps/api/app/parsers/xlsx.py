"""Read XLSX worksheet records without evaluating formulas."""

from collections.abc import Iterable
from io import BytesIO
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from app.parsers.table import row_block
from app.schemas.parsed import Block, ParsedDocument
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException


def parse_xlsx(data: bytes, doc_type: str) -> ParsedDocument:
    blocks: list[Block] = []
    warnings: list[str] = []
    try:
        book = load_workbook(BytesIO(data), read_only=True, data_only=True, keep_links=False)
        try:
            for sheet in book.worksheets:
                sheet.reset_dimensions()
                sheet_blocks, partial = _read_sheet(sheet.title, sheet.iter_rows(values_only=True))
                blocks.extend(sheet_blocks)
                if partial:
                    warnings.append(f"{sheet.title}: empty cells or missing column names.")
        finally:
            book.close()
    except (BadZipFile, InvalidFileException, KeyError, OSError, ParseError, ValueError) as exc:
        raise ValueError("The workbook could not be read as XLSX.") from exc
    return ParsedDocument(doc_type, "vi", blocks, warnings)


def _read_sheet(title: str, rows: Iterable[tuple[object, ...]]) -> tuple[list[Block], bool]:
    headers: list[str | None] = []
    records: list[tuple[int, list[str | None]]] = []
    width = 0
    for number, cells in enumerate(rows, start=1):
        values = [None if cell is None else str(cell).strip() or None for cell in cells]
        if not any(values):
            continue
        width = max(width, len(values))
        if not headers:
            headers = values
        else:
            records.append((number, values))
    names = _column_names(headers, width)
    partial = len(headers) != width or headers != names
    blocks = []
    for number, values in records:
        fields = dict(zip(names, values + [None] * (width - len(values)), strict=True))
        partial |= None in fields.values()
        blocks.append(row_block(fields, {"sheet": title, "row": number}))
    return blocks, partial


def _column_names(headers: list[str | None], width: int) -> list[str]:
    names: dict[str, None] = {}
    for index in range(width):
        label = headers[index] if index < len(headers) else None
        column = get_column_letter(index + 1)
        unique = label or f"Column {column}"
        while unique in names:
            unique = f"{unique} ({column})"
        names[unique] = None
    return list(names)
