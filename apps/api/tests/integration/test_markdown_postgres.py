"""Exercise ingestion, versioning and citation against migrated pgvector."""

import json
import os
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from app.container import build_container
from app.db.models import ChunkRow
from app.db.repositories.documents import PostgresDocumentStore
from app.db.workspace import migrated_workspace
from app.main import create_app
from app.settings import Settings
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from tests.fakes.clients import ScriptedLLM, TaggedEmbedder

_API_ROOT = Path(__file__).resolve().parents[2]
_REFUND = _API_ROOT / "tests" / "fixtures" / "refund.md"


@pytest.fixture
def migrated_database() -> Iterator[sessionmaker[Session]]:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for the pgvector integration test")
    with migrated_workspace(database_url) as sessions:
        yield sessions


def test_markdown_versions_and_citation(
    migrated_database: sessionmaker[Session], tmp_path: Path
) -> None:
    settings = Settings(raw_dir=tmp_path, embedding_backend="hash")
    llm = ScriptedLLM()
    container = replace(
        build_container(settings),
        store=PostgresDocumentStore(migrated_database),
        embedder=TaggedEmbedder(),
        llm=llm,
    )
    original = _REFUND.read_bytes()
    updated = original.replace("qua tổng đài".encode(), "qua ứng dụng".encode())
    with TestClient(create_app(container)) as client, migrated_database() as session:
        first = _upload(client, original)
        assert client.get(f"/v1/jobs/{first}").json()["status"] == "ready"
        count = session.scalar(select(func.count()).select_from(ChunkRow))
        assert count == 3
        assert _upload(client, original) == first
        assert session.scalar(select(func.count()).select_from(ChunkRow)) == count

        second = _upload(client, updated)
        assert second != first
        listings = client.get("/v1/documents").json()
        assert {row["version_id"]: row["version"] for row in listings} == {first: 1, second: 2}
        search = select(ChunkRow.version_id).where(ChunkRow.is_active.is_(True)).distinct()
        assert session.scalars(search).all() == [second]

        events = _query(client, "refund")
        assert len(events["retrieval"]) == count
        source = events["retrieval"][0]
        assert "qua ứng dụng" in source["text"]
        assert all("qua tổng đài" not in hit["text"] for hit in events["retrieval"])
        claim = events["final"]["claims"][0]
        assert claim["status"] == "verified"
        assert claim["sources"][0]["chunk_id"] == source["chunk_id"]
        assert claim["sources"][0]["section_path"] == ["Hoàn tiền", "3.2 Điều kiện"]
        assert claim["sources"][0]["loc"] == {"paragraph_idx": 1}

        refused = _query(client, "checkout")
        assert refused["final"]["insufficient_evidence"] is True
        assert llm.calls == 1


def _upload(client: TestClient, content: bytes) -> str:
    response = client.post(
        "/v1/documents",
        files={"file": (_REFUND.name, content, "text/markdown")},
        data={"doc_type": "brd", "module": "refund"},
    )
    assert response.status_code == 202
    return str(response.json()["job_id"])


def _query(client: TestClient, module: str) -> dict[str, Any]:
    response = client.post("/v1/query", json={"query": "điều kiện hoàn tiền", "module": module})
    assert response.status_code == 200
    events = {}
    for block in response.text.strip().split("\n\n"):
        name, data = block.split("\n", 1)
        events[name.removeprefix("event: ")] = json.loads(data.removeprefix("data: "))
    return events
