"""Render table rows consistently across spreadsheet formats."""

from app.schemas.parsed import Block, SourceLocation


def row_block(fields: dict[str, str | None], loc: SourceLocation) -> Block:
    text = "\n".join(f"{name}: {value}" for name, value in fields.items() if value is not None)
    section_path = [sheet] if isinstance(sheet := loc.get("sheet"), str) else []
    return Block("row", text, None, section_path, loc, fields)
