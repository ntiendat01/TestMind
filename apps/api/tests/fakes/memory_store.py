"""In-memory document store for API tests."""

from __future__ import annotations

from app.core.ids import new_id
from app.schemas.parsed import ChunkDraft
from app.schemas.records import SearchHit, StoredChunk, StoredVersion


class MemoryDocumentStore:
    def __init__(self) -> None:
        self.versions: dict[str, StoredVersion] = {}
        self.chunks: dict[str, StoredChunk] = {}
        self._vectors: dict[str, list[float]] = {}
        self.queries: list[dict[str, object]] = []

    def find_ready_by_hash(self, content_hash: str) -> StoredVersion | None:
        for version in self.versions.values():
            if version.content_hash == content_hash and version.status == "ready":
                return version
        return None

    def get_version(self, version_id: str) -> StoredVersion | None:
        return self.versions.get(version_id)

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
        del embedding_model
        document_id = self._document_id(name, doc_type, module)
        self._deactivate(document_id)
        version_number = self._next_version(document_id)
        for draft, chunk_id, vector in chunks:
            self.chunks[chunk_id] = StoredChunk(
                id=chunk_id,
                version_id=version_id,
                ordinal=draft.ordinal,
                text=draft.text,
                section_path=draft.section_path,
                loc=dict(draft.loc),
                requirement_ids=draft.requirement_ids,
                token_count=draft.token_count,
                is_active=True,
                doc_type=doc_type,
                module=module,
                document_name=name,
            )
            self._vectors[chunk_id] = vector
        version = StoredVersion(
            id=version_id,
            document_id=document_id,
            document_name=name,
            doc_type=doc_type,
            module=module,
            version=version_number,
            content_hash=content_hash,
            is_active=True,
            status="ready",
            error=None,
            progress=100,
            chunk_count=len(chunks),
        )
        self.versions[version_id] = version
        return version

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
        document_id = self._document_id(name, doc_type, module)
        version = StoredVersion(
            id=version_id,
            document_id=document_id,
            document_name=name,
            doc_type=doc_type,
            module=module,
            version=self._next_version(document_id),
            content_hash=content_hash,
            is_active=False,
            status="failed",
            error=error,
            progress=0,
            chunk_count=0,
        )
        self.versions[version_id] = version
        return version

    def search_dense(
        self,
        vector: list[float],
        limit: int,
        doc_types: list[str] | None,
        module: str | None,
    ) -> list[SearchHit]:
        hits: list[SearchHit] = []
        for chunk in self.chunks.values():
            if not chunk.is_active:
                continue
            if doc_types and chunk.doc_type not in doc_types:
                continue
            if module is not None and chunk.module != module:
                continue
            hits.append(SearchHit(chunk=chunk, score=_cosine(vector, self._vectors[chunk.id])))
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:limit]

    def save_query(self, **kwargs: object) -> None:
        self.queries.append(kwargs)

    def _document_id(self, name: str, doc_type: str, module: str | None) -> str:
        for version in self.versions.values():
            same_name = version.document_name == name and version.doc_type == doc_type
            if same_name and version.module == module:
                return version.document_id
        return new_id()

    def _next_version(self, document_id: str) -> int:
        numbers = [
            item.version for item in self.versions.values() if item.document_id == document_id
        ]
        return (max(numbers) if numbers else 0) + 1

    def _deactivate(self, document_id: str) -> None:
        inactive: list[str] = []
        for version in self.versions.values():
            if version.document_id == document_id and version.is_active:
                inactive.append(version.id)
                self.versions[version.id] = StoredVersion(
                    id=version.id,
                    document_id=version.document_id,
                    document_name=version.document_name,
                    doc_type=version.doc_type,
                    module=version.module,
                    version=version.version,
                    content_hash=version.content_hash,
                    is_active=False,
                    status=version.status,
                    error=version.error,
                    progress=version.progress,
                    chunk_count=version.chunk_count,
                )
        for chunk_id, chunk in list(self.chunks.items()):
            if chunk.version_id in inactive:
                self.chunks[chunk_id] = StoredChunk(
                    id=chunk.id,
                    version_id=chunk.version_id,
                    ordinal=chunk.ordinal,
                    text=chunk.text,
                    section_path=chunk.section_path,
                    loc=chunk.loc,
                    requirement_ids=chunk.requirement_ids,
                    token_count=chunk.token_count,
                    is_active=False,
                    doc_type=chunk.doc_type,
                    module=chunk.module,
                    document_name=chunk.document_name,
                )


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))
