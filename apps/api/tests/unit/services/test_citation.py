"""Citation membership check."""

from app.schemas.records import SearchHit, StoredChunk
from app.services.generation.citation_check import ClaimIn, LLMAnswer, check_citations


def test_unknown_chunk_id_is_unverified() -> None:
    hit = SearchHit(chunk=_chunk("known"), score=1)
    answer = LLMAnswer(
        claims=[ClaimIn(text="một ý", chunk_ids=["missing"])],
    )
    checked = check_citations(answer, [hit])
    assert checked[0].status == "unverified"
    assert checked[0].chunk_ids == []


def _chunk(chunk_id: str) -> StoredChunk:
    return StoredChunk(
        id=chunk_id,
        version_id="v",
        ordinal=0,
        text="nội dung",
        section_path=("3.2 Điều kiện",),
        loc={"paragraph_idx": 1},
        requirement_ids=(),
        token_count=2,
        is_active=True,
        doc_type="brd",
        module=None,
        document_name="refund.md",
    )
