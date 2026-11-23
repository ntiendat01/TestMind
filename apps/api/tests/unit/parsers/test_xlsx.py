"""Keep worksheet titles, row numbers and missing cells in XLSX records."""

from io import BytesIO

from app.chunking.structure_aware import chunk_document
from app.chunking.tokens import ApproximateTokenCounter
from app.parsers.xlsx import parse_xlsx
from app.schemas.parsed import ChunkConfig
from openpyxl import Workbook


def test_xlsx_chunk_locator_and_missing_cells() -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Điều kiện hoàn tiền"
    sheet.append([None, None, None])
    sheet.append(["tc_key", "title", None])
    sheet.append(["TC-045", "Hoàn tiền", None])
    sheet.merge_cells("B3:C3")
    sheet.append([None, None, None])
    sheet.append(["TC-046", None, "Khác"])
    second = workbook.create_sheet("Đơn hàng")
    second.append(["tc_key", "title"])
    second.append(["TC-047", "Đơn đã giao"])
    output = BytesIO()
    workbook.save(output)
    workbook.close()

    parsed = parse_xlsx(output.getvalue(), "testcase")
    assert len(parsed.warnings) == 1
    assert parsed.blocks[0].fields == {"tc_key": "TC-045", "title": "Hoàn tiền", "Column C": None}
    assert parsed.blocks[1].fields == {"tc_key": "TC-046", "title": None, "Column C": "Khác"}
    chunks = chunk_document(
        parsed, "refund.xlsx", ChunkConfig(400, 800, 50), ApproximateTokenCounter()
    )
    assert [chunk.loc for chunk in chunks] == [
        {"sheet": "Điều kiện hoàn tiền", "row": 3},
        {"sheet": "Điều kiện hoàn tiền", "row": 5},
        {"sheet": "Đơn hàng", "row": 2},
    ]
    assert chunks[0].section_path == ("Điều kiện hoàn tiền",)
