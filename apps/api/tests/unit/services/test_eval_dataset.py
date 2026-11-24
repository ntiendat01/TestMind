"""Check draft labels against corpus positions independently of embedding."""

from pathlib import Path

from app.chunking.structure_aware import chunk_document
from app.chunking.tokens import ApproximateTokenCounter
from app.parsers.csv import parse_csv
from app.parsers.md import parse_text
from app.schemas.parsed import ChunkConfig
from app.services.eval.runner import load_questions

_DATASET = Path(__file__).resolve().parents[5] / "eval" / "datasets" / "refund-checkout"


def test_draft_labels_resolve_to_existing_corpus_sources() -> None:
    known = set()
    for path in (_DATASET / "corpus").iterdir():
        text = path.read_text()
        parsed = (
            parse_csv(text, "testcase")
            if path.suffix == ".csv"
            else parse_text(
                text,
                "brd",
                markdown=True,
            )
        )
        chunks = chunk_document(
            parsed, path.name, ChunkConfig(400, 800, 50), ApproximateTokenCounter()
        )
        for chunk in chunks:
            suffix = (
                f"row:{chunk.loc['row']}"
                if path.suffix == ".csv"
                else " > ".join(
                    chunk.section_path,
                )
            )
            known.add(f"{path.name}#{suffix}")
    dev = load_questions(_DATASET / "dev.jsonl")
    adversarial = load_questions(_DATASET / "adversarial.jsonl")
    draft = load_questions(_DATASET / "holdout_draft.jsonl")
    assert len(dev) == 60
    assert sum(not item.answerable for item in dev) == 15
    assert len(adversarial) == 10
    assert len(draft) == 20
    assert sum(not item.answerable for item in draft) == 5
    assert not {q.question.casefold() for q in draft} & {
        q.question.casefold() for q in dev + adversarial
    }
    for item in dev + adversarial + draft:
        assert set(item.gold_chunks) <= known, item.id
        assert bool(item.gold_answer_points) == item.answerable
