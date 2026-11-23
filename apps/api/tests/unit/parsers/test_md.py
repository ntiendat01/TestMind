"""Markdown parser tests."""

from app.parsers.md import parse_text

_SAMPLE = """# Hoàn tiền

## 3.2 Điều kiện

Khách được hoàn tiền trong 7 ngày.
"""


def test_heading_path_includes_parents() -> None:
    parsed = parse_text(_SAMPLE, "brd", markdown=True)
    paragraph = next(block for block in parsed.blocks if block.kind == "paragraph")
    assert paragraph.section_path == ["Hoàn tiền", "3.2 Điều kiện"]
    assert paragraph.loc["paragraph_idx"] == 2


def test_plain_text_is_one_paragraph() -> None:
    parsed = parse_text("Một đoạn duy nhất.", "process", markdown=False)
    assert len(parsed.blocks) == 1
    assert parsed.blocks[0].section_path == []
