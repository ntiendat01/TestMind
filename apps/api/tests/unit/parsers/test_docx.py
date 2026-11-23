"""Golden Word fixture for sequential blocks and split table sources."""

from io import BytesIO

from app.chunking.structure_aware import chunk_document
from app.chunking.tokens import ApproximateTokenCounter
from app.parsers.docx import parse_docx
from app.schemas.parsed import ChunkConfig
from docx import Document


def test_docx_preserves_block_order_and_repeats_table_headers() -> None:
    document = Document()
    document.add_heading("Hoàn tiền", 1)
    document.add_heading("Điều kiện", 2)
    document.add_paragraph("Quy định áp dụng cho thanh toán trực tuyến.")
    table = document.add_table(rows=3, cols=2)
    records = [
        ("Mã", "Quy tắc"),
        ("REQ-045", "Hoàn tiền khi đơn chưa giao"),
        ("REQ-046", "Từ chối khi đơn đã sử dụng"),
    ]
    for row, record in zip(table.rows, records, strict=True):
        for cell, text in zip(row.cells, record, strict=True):
            cell.text = text
    document.add_paragraph("Thời gian xử lý là bảy ngày.")
    content = BytesIO()
    document.save(content)

    parsed = parse_docx(content.getvalue(), "brd")
    assert [block.kind for block in parsed.blocks] == [
        "heading",
        "heading",
        "paragraph",
        "table",
        "paragraph",
    ]
    assert parsed.blocks[3].section_path == ["Hoàn tiền", "Điều kiện"]
    chunks = chunk_document(
        parsed, "refund.docx", ChunkConfig(20, 20, 0), ApproximateTokenCounter()
    )
    table_chunks = [chunk for chunk in chunks if "row" in chunk.loc]
    assert [chunk.loc for chunk in table_chunks] == [
        {"paragraph_idx": 3, "row": 2},
        {"paragraph_idx": 3, "row": 3},
    ]
    assert [chunk.text for chunk in table_chunks] == [
        "Mã: REQ-045 | Quy tắc: Hoàn tiền khi đơn chưa giao",
        "Mã: REQ-046 | Quy tắc: Từ chối khi đơn đã sử dụng",
    ]
    assert chunks[-1].loc == {"paragraph_idx": 4}
