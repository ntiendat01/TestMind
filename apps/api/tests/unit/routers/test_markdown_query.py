"""Upload a Markdown note and read a cited answer without calling Forge."""

import json
from pathlib import Path

from app.chunking.tokens import ApproximateTokenCounter
from app.container import Container
from app.main import create_app
from app.schemas.parsed import ChunkConfig
from app.settings import Settings, discover_config_dir, load_answer_prompt
from fastapi.testclient import TestClient
from tests.fakes.clients import BrokenLLM, ScriptedLLM, TaggedEmbedder
from tests.fakes.memory_store import MemoryDocumentStore

_MARKDOWN = """# Hoàn tiền

## 3.2 Điều kiện

Khách được hoàn tiền trong 7 ngày nếu đơn chưa giao.

## 3.3 Ngoài phạm vi

Không áp dụng cho hàng đã sử dụng.
"""


def test_query_cites_the_matching_section(tmp_path: Path) -> None:
    llm = ScriptedLLM()
    client = TestClient(_app(tmp_path, llm))
    uploaded = client.post(
        "/v1/documents",
        files={"file": ("refund.md", _MARKDOWN.encode(), "text/markdown")},
        data={"doc_type": "brd"},
    )
    assert uploaded.status_code == 202
    job_id = uploaded.json()["job_id"]
    again = client.post(
        "/v1/documents",
        files={"file": ("refund.md", _MARKDOWN.encode(), "text/markdown")},
        data={"doc_type": "brd"},
    )
    assert again.json()["job_id"] == job_id
    job = client.get(f"/v1/jobs/{job_id}")
    assert job.json()["status"] == "ready"
    assert job.json()["chunk_count"] >= 1
    listed = client.get("/v1/documents")
    assert listed.json()[0]["name"] == "refund.md"

    response = client.post("/v1/query", json={"query": "điều kiện hoàn tiền"})
    assert response.status_code == 200
    final = _event(response.text, "final")
    assert final["insufficient_evidence"] is False
    claim = final["claims"][0]
    assert claim["status"] == "verified"
    assert "3.2 Điều kiện" in claim["sources"][0]["section_path"]
    assert llm.calls == 1


def test_unknown_chunk_is_unverified_after_retry(tmp_path: Path) -> None:
    llm = BrokenLLM()
    client = TestClient(_app(tmp_path, llm))
    client.post(
        "/v1/documents",
        files={"file": ("refund.md", _MARKDOWN.encode(), "text/markdown")},
        data={"doc_type": "brd"},
    )
    response = client.post("/v1/query", json={"query": "hoàn tiền"})
    final = _event(response.text, "final")
    assert final["claims"][0]["status"] == "unverified"
    assert llm.calls == 2


def test_docx_is_rejected(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path, ScriptedLLM()))
    response = client.post(
        "/v1/documents",
        files={"file": ("cases.docx", b"PK", "application/octet-stream")},
        data={"doc_type": "testcase"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_type"


def test_no_chunks_does_not_call_the_model(tmp_path: Path) -> None:
    llm = ScriptedLLM()
    client = TestClient(_app(tmp_path, llm))
    response = client.post("/v1/query", json={"query": "hoàn tiền"})
    final = _event(response.text, "final")
    assert final["insufficient_evidence"] is True
    assert llm.calls == 0


def test_ingest_failure_is_a_controlled_error(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path, ScriptedLLM(), embedder=_Boom()))
    response = client.post(
        "/v1/documents",
        files={"file": ("refund.md", _MARKDOWN.encode(), "text/markdown")},
        data={"doc_type": "brd"},
    )
    assert response.status_code == 500
    assert response.json()["code"] == "ingest_failed"


class _Boom:
    model_name = "boom"

    def embed(self, texts: list[str]) -> list[list[float]]:
        del texts
        raise RuntimeError("embed down")


def _app(tmp_path: Path, llm: ScriptedLLM | BrokenLLM, embedder: object | None = None) -> object:
    version, prompt = load_answer_prompt(discover_config_dir())
    container = Container(
        settings=Settings(raw_dir=tmp_path, max_upload_bytes=20_000),
        store=MemoryDocumentStore(),
        embedder=embedder or TaggedEmbedder(),
        llm=llm,
        counter=ApproximateTokenCounter(),
        chunk_config=ChunkConfig(400, 800, 50),
        prompt_version=version,
        prompt_text=prompt,
        raw_dir=tmp_path,
    )
    return create_app(container)


def _event(body: str, name: str) -> dict[str, object]:
    marker = f"event: {name}\n"
    start = body.index(marker) + len(marker)
    data_line = body[start:].split("\n", 1)[0]
    payload = json.loads(data_line.removeprefix("data: "))
    assert isinstance(payload, dict)
    return payload
