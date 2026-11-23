"""Upload a Markdown note and read a cited answer without calling Forge."""

import json
from io import BytesIO
from pathlib import Path

from app.chunking.tokens import ApproximateTokenCounter
from app.container import Container
from app.main import create_app
from app.schemas.parsed import ChunkConfig
from app.settings import Settings, discover_config_dir, load_answer_prompt
from docx import Document
from fastapi.testclient import TestClient
from openpyxl import Workbook
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


def test_invalid_docx_is_rejected(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path, ScriptedLLM()))
    response = client.post(
        "/v1/documents",
        files={"file": ("cases.docx", b"PK", "application/octet-stream")},
        data={"doc_type": "testcase"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_docx"


def test_csv_upload_and_citation_keep_source_row(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path, ScriptedLLM()))
    data = "\ufeffid,title\nTC-01,Điều kiện hoàn tiền\nTC-02,Đơn đã giao".encode()
    uploaded = client.post(
        "/v1/documents",
        files={"file": ("refund.csv", data, "text/csv")},
        data={"doc_type": "testcase"},
    )
    assert uploaded.status_code == 202
    assert client.get(f"/v1/jobs/{uploaded.json()['job_id']}").json()["chunk_count"] == 2

    response = client.post("/v1/query", json={"query": "điều kiện hoàn tiền"})
    final = _event(response.text, "final")
    assert final["claims"][0]["sources"][0]["loc"] == {"row": 2}


def test_xlsx_upload_and_citation_keep_sheet_and_row(tmp_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Refund"
    sheet.append(["id", "title"])
    sheet.append(["TC-01", "Điều kiện hoàn tiền"])
    output = BytesIO()
    workbook.save(output)
    workbook.close()

    client = TestClient(_app(tmp_path, ScriptedLLM()))
    uploaded = client.post(
        "/v1/documents",
        files={"file": ("refund.xlsx", output.getvalue(), "application/octet-stream")},
        data={"doc_type": "testcase"},
    )
    assert uploaded.status_code == 202
    response = client.post("/v1/query", json={"query": "điều kiện hoàn tiền"})
    final = _event(response.text, "final")
    assert final["claims"][0]["sources"][0]["loc"] == {"sheet": "Refund", "row": 2}


def test_rejects_invalid_xlsx_container(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path, ScriptedLLM()))
    uploaded = client.post(
        "/v1/documents",
        files={"file": ("refund.xlsx", b"not an archive", "application/octet-stream")},
        data={"doc_type": "testcase"},
    )
    assert uploaded.status_code == 400
    assert uploaded.json()["code"] == "invalid_xlsx"


def test_docx_upload_and_citation_keep_section_and_block(tmp_path: Path) -> None:
    document = Document()
    document.add_heading("Điều kiện hoàn tiền", 1)
    document.add_paragraph("Khách được hoàn tiền trong 7 ngày.")
    output = BytesIO()
    document.save(output)

    client = TestClient(_app(tmp_path, ScriptedLLM(), max_upload_bytes=1_000_000))
    uploaded = client.post(
        "/v1/documents",
        files={"file": ("refund.docx", output.getvalue(), "application/octet-stream")},
        data={"doc_type": "brd"},
    )
    assert uploaded.status_code == 202
    response = client.post("/v1/query", json={"query": "điều kiện hoàn tiền"})
    final = _event(response.text, "final")
    assert final["claims"][0]["sources"][0]["loc"] == {"paragraph_idx": 0}
    assert final["claims"][0]["sources"][0]["section_path"] == ["Điều kiện hoàn tiền"]


def test_rejects_mismatched_upload_media_type(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path, ScriptedLLM()))
    uploaded = client.post(
        "/v1/documents",
        files={"file": ("refund.csv", b"id,title", "image/png")},
        data={"doc_type": "testcase"},
    )
    assert uploaded.status_code == 400
    assert uploaded.json()["code"] == "invalid_media_type"


def test_no_chunks_does_not_call_the_model(tmp_path: Path) -> None:
    llm = ScriptedLLM()
    client = TestClient(_app(tmp_path, llm))
    response = client.post("/v1/query", json={"query": "hoàn tiền"})
    final = _event(response.text, "final")
    assert final["insufficient_evidence"] is True
    assert llm.calls == 0


def test_low_scoring_hits_are_returned_without_calling_the_model(tmp_path: Path) -> None:
    llm = ScriptedLLM()
    app = _app(tmp_path, llm, min_similarity=0.5)
    client = TestClient(app)
    client.post(
        "/v1/documents",
        files={"file": ("refund.csv", b"id,title\nTC-01,Policy", "text/csv")},
        data={"doc_type": "testcase"},
    )
    response = client.post("/v1/query", json={"query": "điều kiện hoàn tiền"})
    assert _event(response.text, "final")["insufficient_evidence"] is True
    assert '"loc": {"row": 2}' in response.text
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


def _app(
    tmp_path: Path,
    llm: ScriptedLLM | BrokenLLM,
    embedder: object | None = None,
    *,
    min_similarity: float | None = None,
    max_upload_bytes: int = 20_000,
) -> object:
    version, prompt = load_answer_prompt(discover_config_dir())
    container = Container(
        settings=Settings(
            raw_dir=tmp_path,
            max_upload_bytes=max_upload_bytes,
            retrieval_min_similarity=min_similarity,
        ),
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
