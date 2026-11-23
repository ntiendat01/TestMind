"""Structure-aware packing."""

from app.chunking.structure_aware import chunk_document
from app.parsers.md import parse_text
from app.schemas.parsed import ChunkConfig


class WordCounter:
    def count(self, text: str) -> int:
        return len(text.split())


def test_splits_on_target_and_keeps_requirement_id() -> None:
    first = " ".join(f"từ{index}" for index in range(4))
    second = " ".join(f"khác{index}" for index in range(4))
    text = f"# Quy định\n\n{first} REQ-045\n\n{second}"
    parsed = parse_text(text, "brd", markdown=True)
    drafts = chunk_document(parsed, "refund.md", ChunkConfig(3, 8, 1), WordCounter())
    assert len(drafts) >= 2
    assert any("REQ-045" in draft.requirement_ids for draft in drafts)
    assert drafts[0].text_for_embedding.startswith("refund.md >")
