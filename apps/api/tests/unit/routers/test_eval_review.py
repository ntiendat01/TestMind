"""Exercise review imports without database, filesystem writes or LLM calls."""

import json
from pathlib import Path

import pytest
from app.main import create_app
from app.routers.eval import MAX_REVIEW_BYTES
from fastapi.testclient import TestClient

REPORTS = Path(__file__).resolve().parents[5] / "eval/reports"
CLIENT = TestClient(create_app())
PREFIX = "/v1/eval/review"


def packet() -> list[dict[str, object]]:
    content = (REPORTS / "m2-qa40.cases.jsonl").read_text()
    response = CLIENT.post(f"{PREFIX}/packet", json={"content": content})
    assert response.status_code == 200
    return response.json()  # type: ignore[no-any-return]


def test_existing_packet_and_pending_templates_roundtrip() -> None:
    cases = packet()
    assert len(cases) == 80
    content = (REPORTS / "m2-qa40.reviewer-a.jsonl").read_text()
    result = CLIENT.post(f"{PREFIX}/scores/validate", json={"cases": cases, "content": content})
    assert result.status_code == 200
    assert len(result.json()) == 80
    assert all(score["answer_correctness"] is None for score in result.json())
    pending = result.json()[0]
    pending["comments"] = "Notes-only draft, not a completed review."
    result = CLIENT.post(
        f"{PREFIX}/scores/validate", json={"cases": cases, "content": json.dumps(pending)}
    )
    assert result.status_code == 200
    assert result.json()[0]["comments"] == pending["comments"]


@pytest.mark.parametrize("change", ["digest", "duplicate", "json", "empty", "too_many"])
def test_packet_rejects_corruption_and_oversized_case_lists(change: str) -> None:
    cases = packet()
    if change == "digest":
        cases[0]["observation_sha256"] = "changed"
    if change == "duplicate":
        cases.append(cases[0])
    if change == "too_many":
        cases = [{**cases[0], "case_id": str(i)} for i in range(501)]
    content = "\n".join(json.dumps(case) for case in cases)
    content = {"json": "{", "empty": " "}.get(change, content)
    result = CLIENT.post(f"{PREFIX}/packet", json={"content": content})
    assert result.status_code == 422
    assert result.json()["code"] == "invalid_review_packet"


def test_scores_bind_to_observations_and_keep_partial_ratings() -> None:
    cases = packet()
    score = {
        "case_id": cases[0]["case_id"],
        "observation_sha256": cases[0]["observation_sha256"],
        "reviewer": " QA fixture ",
        "reviewer_kind": "human",
        "answer_correctness": 0.5,
        "comments": "Test fixture only.",
    }
    payload = {"cases": cases, "content": json.dumps(score)}
    result = CLIENT.post(f"{PREFIX}/scores/validate", json=payload)
    assert result.status_code == 200
    assert result.json()[0]["reviewer"] == "QA fixture"
    assert result.json()[0]["faithfulness"] is None
    for changes in (
        {"observation_sha256": "changed"},
        {"reviewer": " "},
        {"comments": ""},
        {"answer_correctness": True},
    ):
        payload["content"] = json.dumps({**score, **changes})
        assert CLIENT.post(f"{PREFIX}/scores/validate", json=payload).status_code == 422
    payload["content"] = json.dumps(score)
    cases[0]["observation_sha256"] = "changed"
    assert CLIENT.post(f"{PREFIX}/scores/validate", json=payload).status_code == 422


def test_streamed_body_is_bounded_without_content_length() -> None:
    chunks = (b"x" * 1024 * 1024 for _ in range(MAX_REVIEW_BYTES // (1024 * 1024) + 1))
    result = CLIENT.post(f"{PREFIX}/packet", content=chunks)
    assert result.status_code == 413
    assert result.json()["code"] == "review_too_large"
