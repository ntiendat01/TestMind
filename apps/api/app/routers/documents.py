"""Document upload. Markdown only in this slice."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.container import Container
from app.services.ingestion.pipeline import ingest_markdown

router = APIRouter(tags=["documents"])


def get_container(request: Request) -> Container:
    container = request.app.state.container
    if not isinstance(container, Container):
        raise RuntimeError("Application container is not configured.")
    return container


@router.post("/v1/documents", status_code=202)
def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    module: str | None = Form(None),
    container: Container = Depends(get_container),
) -> dict[str, object]:
    data = file.file.read()
    version = ingest_markdown(
        filename=file.filename or "document.md",
        data=data,
        doc_type=doc_type,
        module=module or None,
        store=container.store,
        embedder=container.embedder,
        counter=container.counter,
        config=container.chunk_config,
        max_bytes=container.settings.max_upload_bytes,
        raw_dir=container.raw_dir,
    )
    return {"job_id": version.id, "status": version.status}
