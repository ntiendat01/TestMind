"""Postgres store for documents, chunks, and query logs."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.ids import new_id
from app.db.models import ChunkRow, DocumentRow, DocumentVersionRow, QueryRow
from app.schemas.parsed import ChunkDraft
from app.schemas.records import DocumentSummary, SearchHit, StoredChunk, StoredVersion
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker


class PostgresDocumentStore:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def find_ready_by_hash(self, content_hash: str) -> StoredVersion | None:
        with self._sessions() as session:
            row = session.scalar(
                select(DocumentVersionRow).where(
                    DocumentVersionRow.content_hash == content_hash,
                    DocumentVersionRow.status == "ready",
                )
            )
            return None if row is None else _version(session, row)

    def get_version(self, version_id: str) -> StoredVersion | None:
        with self._sessions() as session:
            row = session.get(DocumentVersionRow, version_id)
            return None if row is None else _version(session, row)

    def list_documents(self) -> list[DocumentSummary]:
        with self._sessions() as session:
            rows = session.execute(
                select(DocumentVersionRow, DocumentRow)
                .join(DocumentRow, DocumentRow.id == DocumentVersionRow.document_id)
                .order_by(DocumentVersionRow.uploaded_at.desc())
                .limit(50)
            ).all()
            summaries: list[DocumentSummary] = []
            for version, document in rows:
                count = session.scalar(
                    select(func.count())
                    .select_from(ChunkRow)
                    .where(ChunkRow.version_id == version.id)
                )
                summaries.append(
                    DocumentSummary(
                        document_id=document.id,
                        name=document.name,
                        doc_type=document.doc_type,
                        module=document.module,
                        version_id=version.id,
                        version=version.version,
                        status=version.status,
                        chunk_count=int(count or 0),
                        error=version.error,
                    )
                )
            return summaries

    def save_ready(
        self,
        *,
        version_id: str,
        name: str,
        doc_type: str,
        module: str | None,
        content_hash: str,
        chunks: list[tuple[ChunkDraft, str, list[float]]],
        embedding_model: str,
    ) -> StoredVersion:
        with self._sessions() as session:
            document = _document(session, name, doc_type, module)
            _deactivate(session, document.id)
            version = _insert_version(session, version_id, document, content_hash)
            for draft, chunk_id, vector in chunks:
                session.add(
                    _chunk_row(
                        draft,
                        chunk_id,
                        vector,
                        version,
                        doc_type,
                        module,
                        embedding_model,
                    )
                )
            session.commit()
            return _version(session, version)

    def mark_failed(
        self,
        *,
        version_id: str,
        name: str,
        doc_type: str,
        module: str | None,
        content_hash: str,
        error: str,
    ) -> StoredVersion:
        with self._sessions() as session:
            document = _document(session, name, doc_type, module)
            version = DocumentVersionRow(
                id=version_id,
                document_id=document.id,
                version=_next_version(session, document.id),
                content_hash=content_hash,
                is_active=False,
                status="failed",
                error=error,
                progress=0,
                uploaded_at=datetime.now(UTC),
            )
            session.add(version)
            session.commit()
            return _version(session, version)

    def search_dense(
        self,
        vector: list[float],
        limit: int,
        doc_types: list[str] | None,
        module: str | None,
    ) -> list[SearchHit]:
        with self._sessions() as session:
            distance = ChunkRow.embedding.cosine_distance(vector)
            stmt = (
                select(ChunkRow, DocumentRow.name, distance.label("distance"))
                .join(DocumentVersionRow, DocumentVersionRow.id == ChunkRow.version_id)
                .join(DocumentRow, DocumentRow.id == DocumentVersionRow.document_id)
                .where(ChunkRow.is_active.is_(True))
                .order_by(distance)
                .limit(limit)
            )
            if doc_types:
                stmt = stmt.where(ChunkRow.doc_type.in_(doc_types))
            if module is not None:
                stmt = stmt.where(ChunkRow.module == module)
            hits: list[SearchHit] = []
            for chunk, document_name, dist in session.execute(stmt):
                hits.append(
                    SearchHit(
                        chunk=_chunk(chunk, str(document_name)),
                        score=1 - float(dist),
                    )
                )
            return hits

    def save_query(
        self,
        *,
        text: str,
        filters: dict[str, object],
        retrieved: list[dict[str, object]],
        answer: str,
        insufficient_evidence: bool,
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        prompt_version: str,
    ) -> None:
        with self._sessions() as session:
            session.add(
                QueryRow(
                    id=new_id(),
                    text=text,
                    filters=filters,
                    retrieved=retrieved,
                    answer=answer,
                    insufficient_evidence=insufficient_evidence,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    latency_ms=latency_ms,
                    prompt_version=prompt_version,
                    created_at=datetime.now(UTC),
                )
            )
            session.commit()


def _document(session: Session, name: str, doc_type: str, module: str | None) -> DocumentRow:
    stmt = select(DocumentRow).where(DocumentRow.name == name, DocumentRow.doc_type == doc_type)
    if module is None:
        stmt = stmt.where(DocumentRow.module.is_(None))
    else:
        stmt = stmt.where(DocumentRow.module == module)
    found = session.scalar(stmt)
    if found is not None:
        return found
    created = DocumentRow(
        id=new_id(),
        name=name,
        doc_type=doc_type,
        module=module,
        created_at=datetime.now(UTC),
    )
    session.add(created)
    session.flush()
    return created


def _next_version(session: Session, document_id: str) -> int:
    numbers = list(
        session.scalars(
            select(DocumentVersionRow.version).where(DocumentVersionRow.document_id == document_id)
        ).all()
    )
    return (max(numbers) if numbers else 0) + 1


def _deactivate(session: Session, document_id: str) -> None:
    version_ids = list(
        session.scalars(
            select(DocumentVersionRow.id).where(
                DocumentVersionRow.document_id == document_id,
                DocumentVersionRow.is_active.is_(True),
            )
        ).all()
    )
    if not version_ids:
        return
    session.execute(
        update(DocumentVersionRow)
        .where(DocumentVersionRow.id.in_(version_ids))
        .values(is_active=False)
    )
    session.execute(
        update(ChunkRow).where(ChunkRow.version_id.in_(version_ids)).values(is_active=False)
    )


def _insert_version(
    session: Session,
    version_id: str,
    document: DocumentRow,
    content_hash: str,
) -> DocumentVersionRow:
    version = DocumentVersionRow(
        id=version_id,
        document_id=document.id,
        version=_next_version(session, document.id),
        content_hash=content_hash,
        is_active=True,
        status="ready",
        error=None,
        progress=100,
        uploaded_at=datetime.now(UTC),
    )
    session.add(version)
    session.flush()
    return version


def _chunk_row(
    draft: ChunkDraft,
    chunk_id: str,
    vector: list[float],
    version: DocumentVersionRow,
    doc_type: str,
    module: str | None,
    embedding_model: str,
) -> ChunkRow:
    return ChunkRow(
        id=chunk_id,
        version_id=version.id,
        ordinal=draft.ordinal,
        text=draft.text,
        text_for_embedding=draft.text_for_embedding,
        section_path=list(draft.section_path),
        loc=draft.loc,
        requirement_ids=list(draft.requirement_ids),
        token_count=draft.token_count,
        embedding=vector,
        embedding_model=embedding_model,
        is_active=True,
        doc_type=doc_type,
        module=module,
    )


def _version(session: Session, row: DocumentVersionRow) -> StoredVersion:
    document = session.get(DocumentRow, row.document_id)
    count = session.scalar(
        select(func.count()).select_from(ChunkRow).where(ChunkRow.version_id == row.id)
    )
    return StoredVersion(
        id=row.id,
        document_id=row.document_id,
        document_name="" if document is None else document.name,
        doc_type="" if document is None else document.doc_type,
        module=None if document is None else document.module,
        version=row.version,
        content_hash=row.content_hash,
        is_active=row.is_active,
        status=row.status,
        error=row.error,
        progress=row.progress,
        chunk_count=int(count or 0),
    )


def _chunk(row: ChunkRow, document_name: str) -> StoredChunk:
    return StoredChunk(
        id=row.id,
        version_id=row.version_id,
        ordinal=row.ordinal,
        text=row.text,
        section_path=tuple(row.section_path),
        loc={str(key): int(value) for key, value in dict(row.loc).items()},
        requirement_ids=tuple(row.requirement_ids),
        token_count=row.token_count,
        is_active=row.is_active,
        doc_type=row.doc_type,
        module=row.module,
        document_name=document_name,
    )
