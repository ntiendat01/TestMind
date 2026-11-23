"""List and upload documents."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.container import Container
from app.services.ingestion.pipeline import ingest_document

router = APIRouter(tags=["documents"])


def get_container(request: Request) -> Container:
    container = request.app.state.container
    if not isinstance(container, Container):
        raise RuntimeError("Application container is not configured.")
    return container


@router.get("/v1/documents")
def list_documents(container: Container = Depends(get_container)) -> list[dict[str, object]]:
    return [
        {
            "document_id": item.document_id,
            "name": item.name,
            "doc_type": item.doc_type,
            "module": item.module,
            "version_id": item.version_id,
            "version": item.version,
            "status": item.status,
            "chunk_count": item.chunk_count,
            "error": item.error,
        }
        for item in container.store.list_documents()
    ]


@router.post("/v1/documents", status_code=202)
def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    module: str | None = Form(None),
    container: Container = Depends(get_container),
) -> dict[str, object]:
    data = file.file.read(container.settings.max_upload_bytes + 1)
    version = ingest_document(
        filename=file.filename or "document.md",
        data=data,
        doc_type=doc_type,
        module=module or None,
        content_type=file.content_type,
        store=container.store,
        embedder=container.embedder,
        counter=container.counter,
        config=container.chunk_config,
        max_bytes=container.settings.max_upload_bytes,
        raw_dir=container.raw_dir,
    )
    return {"job_id": version.id, "status": version.status}
