"""Preserve physical source positions and row boundaries in CSV."""

import pytest
from app.chunking.structure_aware import chunk_document
from app.chunking.tokens import ApproximateTokenCounter
from app.parsers.csv import parse_csv
from app.schemas.parsed import ChunkConfig


def test_chunks_keep_one_csv_record_and_its_start_line() -> None:
    parsed = parse_csv(
        'tc_key,title,expected\r\nTC-01,"điều kiện\r\nhoàn tiền",Được duyệt\r\n\r\nTC-02,Đã giao',
        "testcase",
    )
    chunks = chunk_document(
        parsed, "refund.csv", ChunkConfig(400, 800, 50), ApproximateTokenCounter()
    )
    assert [chunk.loc for chunk in chunks] == [{"row": 2}, {"row": 5}]
    assert chunks[0].text == "tc_key: TC-01\ntitle: điều kiện\r\nhoàn tiền\nexpected: Được duyệt"
    assert chunks[1].text == "tc_key: TC-02\ntitle: Đã giao"


@pytest.mark.parametrize("text", ["key,key\n1,2", "key\n1,2", 'key\n"unterminated'])
def test_rejects_invalid_csv(text: str) -> None:
    with pytest.raises(ValueError):
        parse_csv(text, "testcase")
