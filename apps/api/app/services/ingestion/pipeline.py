"""Parse a document upload into stored chunks."""

from __future__ import annotations

import logging
from pathlib import Path

from app.chunking.structure_aware import chunk_document
from app.core.errors import APIError
from app.core.ids import content_hash, make_chunk_id, new_id
from app.core.interfaces import DocumentStore, Embedder, TokenCounter
from app.parsers.csv import parse_csv
from app.parsers.docx import parse_docx
from app.parsers.md import parse_text
from app.parsers.ooxml import validate_container
from app.parsers.xlsx import parse_xlsx
from app.schemas.parsed import ChunkConfig, ChunkDraft, ParsedDocument
from app.schemas.records import StoredVersion

_LOG = logging.getLogger(__name__)
_DOC_TYPES = {"brd", "srs", "testcase", "bug", "api", "process"}
_MEDIA_TYPES = {
    ".md": {"text/markdown", "text/plain", "text/x-markdown"},
    ".txt": {"text/plain"},
    ".csv": {"text/csv", "text/plain", "application/csv", "application/vnd.ms-excel"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
}
_OFFICE_PARSERS = {".xlsx": parse_xlsx, ".docx": parse_docx}


def ingest_document(
    *,
    filename: str,
    data: bytes,
    doc_type: str,
    module: str | None,
    content_type: str | None,
    store: DocumentStore,
    embedder: Embedder,
    counter: TokenCounter,
    config: ChunkConfig,
    max_bytes: int,
    raw_dir: Path,
) -> StoredVersion:
    suffix = Path(filename).suffix.lower()
    _validate(suffix, data, doc_type, content_type, max_bytes)
    digest = content_hash(data)
    existing = store.find_ready_by_hash(digest)
    if existing is not None:
        return existing
    version_id = new_id()
    try:
        return _index(
            version_id=version_id,
            filename=filename,
            suffix=suffix,
            data=data,
            doc_type=doc_type,
            module=module,
            digest=digest,
            store=store,
            embedder=embedder,
            counter=counter,
            config=config,
            raw_dir=raw_dir,
        )
    except APIError:
        raise
    except Exception as exc:
        _LOG.exception("ingest failed")
        store.mark_failed(
            version_id=version_id,
            name=Path(filename).name,
            doc_type=doc_type,
            module=module,
            content_hash=digest,
            error=str(exc)[:300],
        )
        raise APIError(500, "ingest_failed", "Ingestion failed.") from exc


def _validate(
    suffix: str, data: bytes, doc_type: str, content_type: str | None, max_bytes: int
) -> None:
    if doc_type not in _DOC_TYPES:
        raise APIError(400, "invalid_doc_type", "Unsupported doc_type.")
    if suffix not in _MEDIA_TYPES:
        raise APIError(400, "unsupported_type", "Upload a .md, .txt, .csv, .xlsx or .docx file.")
    media_type = (content_type or "").partition(";")[0].strip().lower()
    if (
        media_type not in {"", "application/octet-stream"}
        and media_type not in _MEDIA_TYPES[suffix]
    ):
        raise APIError(400, "invalid_media_type", "The file type does not match its extension.")
    if not data or len(data) > max_bytes:
        raise APIError(400, "invalid_file", "File is empty or larger than the limit.")
    if suffix in _OFFICE_PARSERS:
        try:
            validate_container(data, max_expanded_bytes=max_bytes * 5)
        except ValueError as exc:
            raise APIError(400, f"invalid_{suffix[1:]}", str(exc)) from exc


def _index(
    *,
    version_id: str,
    filename: str,
    suffix: str,
    data: bytes,
    doc_type: str,
    module: str | None,
    digest: str,
    store: DocumentStore,
    embedder: Embedder,
    counter: TokenCounter,
    config: ChunkConfig,
    raw_dir: Path,
) -> StoredVersion:
    parsed = _parse(data, suffix, doc_type)
    if parsed.warnings:
        _LOG.warning("document parsed with %d format warnings", len(parsed.warnings))
    drafts = chunk_document(parsed, Path(filename).name, config, counter)
    if not drafts:
        raise APIError(400, "empty_document", "The file has no indexable text.")
    vectors = embedder.embed([draft.text_for_embedding for draft in drafts])
    rows = _rows(version_id, drafts, vectors)
    _write_raw(raw_dir, version_id, filename, data)
    return store.save_ready(
        version_id=version_id,
        name=Path(filename).name,
        doc_type=doc_type,
        module=module,
        content_hash=digest,
        chunks=rows,
        embedding_model=embedder.model_name,
    )


def _parse(data: bytes, suffix: str, doc_type: str) -> ParsedDocument:
    if office_parser := _OFFICE_PARSERS.get(suffix):
        try:
            return office_parser(data, doc_type)
        except ValueError as exc:
            raise APIError(400, f"invalid_{suffix[1:]}", str(exc)) from exc
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise APIError(400, "invalid_encoding", "File must be UTF-8.") from exc
    if suffix == ".csv":
        try:
            return parse_csv(text, doc_type)
        except ValueError as exc:
            raise APIError(400, "invalid_csv", str(exc)) from exc
    return parse_text(text, doc_type, markdown=suffix == ".md")


def _rows(
    version_id: str,
    drafts: list[ChunkDraft],
    vectors: list[list[float]],
) -> list[tuple[ChunkDraft, str, list[float]]]:
    rows: list[tuple[ChunkDraft, str, list[float]]] = []
    for draft, vector in zip(drafts, vectors, strict=True):
        chunk_id = make_chunk_id(version_id, draft.loc, draft.ordinal)
        rows.append((draft, chunk_id, vector))
    return rows


def _write_raw(raw_dir: Path, version_id: str, filename: str, data: bytes) -> None:
    target = raw_dir / version_id / Path(filename).name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
