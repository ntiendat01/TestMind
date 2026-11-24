"""Index a synthetic corpus and run the production dense retrieval pipeline."""

import json
from pathlib import Path
from time import perf_counter
from typing import Self

from app.core.interfaces import DocumentStore, Embedder, TokenCounter
from app.schemas.parsed import ChunkConfig
from app.schemas.records import SearchHit
from app.services.eval.metrics import Observation
from app.services.ingestion.pipeline import ingest_document
from app.services.retrieval.pipeline import retrieve_dense
from pydantic import BaseModel, Field, model_validator

_MODULE = "refund-checkout-eval"
_SUFFIXES = {".md", ".txt", ".csv", ".xlsx", ".docx"}


class EvalConfig(BaseModel):
    dataset: str
    embedding_model: str
    retrieval_limit: int = Field(30, gt=0)
    context_token_budget: int = Field(3000, gt=0)
    sufficiency_tau: float | None = Field(default=None, ge=-1, le=1)
    seed: int = 0


class EvalQuestion(BaseModel):
    id: str
    type: str
    lang: str
    question: str = Field(min_length=1)
    gold_chunks: list[str]
    gold_answer_points: list[str] = Field(default_factory=list)
    answerable: bool

    @model_validator(mode="after")
    def check_gold(self) -> Self:
        if self.answerable != bool(self.gold_chunks):
            raise ValueError(
                "Answerable questions need gold chunks and unanswerable ones omit them."
            )
        return self


def load_questions(path: Path) -> list[EvalQuestion]:
    questions = [
        EvalQuestion.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if (
        not questions
        or len({item.id for item in questions}) != len(questions)
        or len({item.question.strip().casefold() for item in questions}) != len(questions)
    ):
        raise ValueError("Evaluation needs at least one question and unique IDs.")
    return questions


def load_config(path: Path) -> EvalConfig:
    return EvalConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))


def evaluate_dense(
    *,
    questions: list[EvalQuestion],
    corpus: Path,
    config: EvalConfig,
    chunk_config: ChunkConfig,
    store: DocumentStore,
    embedder: Embedder,
    counter: TokenCounter,
    raw_dir: Path,
    max_upload_bytes: int,
) -> list[Observation]:
    sources = sorted(file for file in corpus.iterdir() if file.suffix.lower() in _SUFFIXES)
    if not sources:
        raise ValueError(f"No indexable corpus files in {corpus}.")
    for path in sources:
        ingest_document(
            filename=path.name,
            data=path.read_bytes(),
            doc_type="testcase" if path.suffix in {".csv", ".xlsx"} else "brd",
            module=_MODULE,
            content_type=None,
            store=store,
            embedder=embedder,
            counter=counter,
            config=chunk_config,
            max_bytes=max_upload_bytes,
            raw_dir=raw_dir,
        )
    return [
        _observe(item, config=config, store=store, embedder=embedder, counter=counter)
        for item in questions
    ]


def _observe(
    item: EvalQuestion,
    *,
    config: EvalConfig,
    store: DocumentStore,
    embedder: Embedder,
    counter: TokenCounter,
) -> Observation:
    started = perf_counter()
    hits = retrieve_dense(
        question=item.question,
        embedder=embedder,
        store=store,
        counter=counter,
        doc_types=None,
        module=_MODULE,
        limit=config.retrieval_limit,
        token_budget=config.context_token_budget,
    )
    latency_ms = (perf_counter() - started) * 1000
    return Observation(
        id=item.id,
        kind=item.type,
        answerable=item.answerable,
        gold=frozenset(item.gold_chunks),
        retrieved=tuple(dict.fromkeys(_locator(hit) for hit in hits)),
        top_score=hits[0].score if hits else None,
        latency_ms=latency_ms,
        question=item.question,
        expected_points=tuple(item.gold_answer_points),
        sources=tuple(
            {
                "locator": _locator(hit),
                "text": hit.chunk.text,
                "score": hit.score,
                "chunk_id": hit.chunk.id,
            }
            for hit in hits
        ),
    )


def _locator(hit: SearchHit) -> str:
    chunk = hit.chunk
    row = chunk.loc.get("row")
    sheet = chunk.loc.get("sheet")
    if isinstance(row, int) and isinstance(sheet, str):
        return f"{chunk.document_name}#{sheet}!{row}"
    if isinstance(row, int) and not chunk.section_path:
        return f"{chunk.document_name}#row:{row}"
    return f"{chunk.document_name}#{' > '.join(chunk.section_path)}"
