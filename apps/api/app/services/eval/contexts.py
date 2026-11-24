"""Load captured retrieval contexts and construct gold contexts from the same corpus."""

import hashlib
from pathlib import Path

from app.chunking.structure_aware import chunk_document
from app.chunking.tokens import ApproximateTokenCounter
from app.core.ids import make_chunk_id
from app.schemas.parsed import ChunkConfig
from app.schemas.records import SearchHit, StoredChunk
from app.services.eval.runner import EvalQuestion
from app.services.ingestion.pipeline import _parse
from pydantic import BaseModel, Field


class CapturedSource(BaseModel):
    locator: str
    text: str
    score: float
    chunk_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")

    def hit(self) -> SearchHit:
        name, _, location = self.locator.partition("#")
        return SearchHit(
            StoredChunk(
                self.chunk_id,
                "captured",
                0,
                self.text,
                (location,),
                {},
                (),
                0,
                True,
                "brd",
                None,
                name,
            ),
            self.score,
        )


class CapturedQuery(BaseModel):
    id: str
    question: str
    answerable: bool
    sources: list[CapturedSource]


class RetrievalSnapshot(BaseModel):
    metadata: dict[str, object]
    observations: list[CapturedQuery]


def corpus_hash(corpus: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(file for file in corpus.iterdir() if file.is_file()):
        digest.update(path.name.encode())
        digest.update(b"\x00")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def gold_inventory(corpus: Path, config: ChunkConfig) -> dict[str, list[SearchHit]]:
    inventory: dict[str, list[SearchHit]] = {}
    for path in sorted(corpus.iterdir()):
        if path.suffix.lower() not in {".md", ".txt", ".csv", ".xlsx", ".docx"}:
            continue
        parsed = _parse(path.read_bytes(), path.suffix.lower(), "brd")
        for draft in chunk_document(parsed, path.name, config, ApproximateTokenCounter()):
            row = draft.loc.get("row")
            sheet = draft.loc.get("sheet")
            location = " > ".join(draft.section_path)
            if isinstance(row, int) and isinstance(sheet, str):
                location = f"{sheet}!{row}"
            elif isinstance(row, int) and not draft.section_path:
                location = f"row:{row}"
            locator = f"{path.name}#{location}"
            chunk = StoredChunk(
                make_chunk_id(path.name, draft.loc, draft.ordinal),
                "gold",
                draft.ordinal,
                draft.text,
                draft.section_path,
                draft.loc,
                draft.requirement_ids,
                draft.token_count,
                True,
                "brd",
                None,
                path.name,
            )
            inventory.setdefault(locator, []).append(SearchHit(chunk, 1.0))
    return inventory


def paired_contexts(
    questions: list[EvalQuestion],
    snapshot: RetrievalSnapshot,
    inventory: dict[str, list[SearchHit]],
) -> list[tuple[EvalQuestion, str, list[SearchHit]]]:
    captured = {item.id: item for item in snapshot.observations}
    if len(captured) != len(snapshot.observations) or set(captured) != {q.id for q in questions}:
        raise ValueError("Retrieval snapshot question IDs differ from the selected dataset.")
    contexts = []
    for question in questions:
        item = captured[question.id]
        if item.question != question.question or item.answerable != question.answerable:
            raise ValueError(f"Retrieval snapshot differs from question {question.id}.")
        missing = set(question.gold_chunks) - inventory.keys()
        if missing:
            raise ValueError(f"Unresolved gold locators for {question.id}: {sorted(missing)}")
        contexts.append((question, "retrieved", [source.hit() for source in item.sources]))
        gold = [hit for locator in question.gold_chunks for hit in inventory[locator]]
        contexts.append((question, "gold", list({hit.chunk.id: hit for hit in gold}.values())))
    return contexts
