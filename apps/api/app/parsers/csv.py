"""Parse comma-delimited UTF-8 records with physical source line numbers."""

import csv
from io import StringIO
from itertools import zip_longest

from app.parsers.table import row_block
from app.schemas.parsed import ParsedDocument


def parse_csv(text: str, doc_type: str) -> ParsedDocument:
    if "\x00" in text:
        raise ValueError("CSV must contain plain text.")
    reader = csv.reader(StringIO(text, newline=""), strict=True)
    try:
        headers = [value.strip() for value in next(reader, [])]
        if not headers or "" in headers or len(set(headers)) != len(headers):
            raise ValueError("CSV needs a header row with unique, non-empty column names.")
        blocks = []
        while True:
            line = reader.line_num + 1
            values = next(reader, None)
            if values is None:
                break
            if not any(value.strip() for value in values):
                continue
            if len(values) > len(headers):
                raise ValueError(f"CSV record on line {line} has more fields than the header.")
            fields = {
                name: value.strip() or None
                for name, value in zip_longest(headers, values, fillvalue="")
            }
            blocks.append(row_block(fields, {"row": line}))
    except csv.Error as exc:
        raise ValueError(f"CSV parsing failed near line {reader.line_num}.") from exc
    return ParsedDocument(doc_type, "vi", blocks)
