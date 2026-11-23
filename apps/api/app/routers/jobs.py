"""Indexing job status. job_id is the document version id."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.container import Container
from app.core.errors import APIError
from app.routers.documents import get_container

router = APIRouter(tags=["jobs"])


@router.get("/v1/jobs/{job_id}")
def read_job(job_id: str, container: Container = Depends(get_container)) -> dict[str, object]:
    version = container.store.get_version(job_id)
    if version is None:
        raise APIError(404, "job_not_found", "Unknown job.")
    return {
        "job_id": version.id,
        "status": version.status,
        "progress": version.progress,
        "error": version.error,
        "chunk_count": version.chunk_count,
    }
