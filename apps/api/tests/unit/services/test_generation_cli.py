"""Exercise CLI snapshot validation, paired execution and partial provider failure."""

import importlib.util
import json
from pathlib import Path

import pytest
from app.core.errors import APIError
from app.services.eval.contexts import CapturedSource
from tests.fakes.clients import ScriptedLLM

_ROOT = Path(__file__).resolve().parents[5]


def _cli(monkeypatch: pytest.MonkeyPatch, output: Path, *extra: str):
    spec = importlib.util.spec_from_file_location(
        "generation_cli", _ROOT / "eval" / "generation.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("LLM_API_KEY", "fake-test-key")
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    monkeypatch.delenv("TESTMIND_EVAL_DATABASE_URL", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "generation",
            "--retrieval-report",
            str(_ROOT / "eval/reports/m2-dense-adversarial.json"),
            "--output",
            str(output),
            *extra,
        ],
    )
    return module


def test_cli_replays_paired_contexts_without_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "generation"
    cli = _cli(monkeypatch, output, "--limit", "2")
    fake = ScriptedLLM()
    monkeypatch.setattr(cli, "InferenceLLMClient", lambda **kwargs: fake)
    assert cli.main() == 0
    report = json.loads(output.with_suffix(".json").read_text())
    assert report["metadata"]["planned_samples"] == 4
    assert report["metadata"]["complete"] is True
    assert report["metadata"]["config"]["limit"] == 2
    assert len(report["observations"]) == fake.calls == 4
    assert report["metrics"]["retrieved"]["samples"] == 2
    assert report["metrics"]["gold"]["samples"] == 2
    assert len(output.with_suffix(".checkpoint.jsonl").read_text().splitlines()) == 4


def test_cli_saves_partial_report_after_repeated_provider_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Unavailable:
        def complete(self, **kwargs):
            raise APIError(502, "llm_unavailable", "provider failure")

    output = tmp_path / "failed"
    cli = _cli(monkeypatch, output)
    monkeypatch.setattr(cli, "InferenceLLMClient", lambda **kwargs: Unavailable())
    assert cli.main() == 1
    report = json.loads(output.with_suffix(".json").read_text())
    assert report["metadata"]["complete"] is False
    assert report["metadata"]["attempted_samples"] == 3
    assert report["metadata"]["planned_samples"] == 20
    assert report["metrics"]["retrieved"]["errors"] == 2
    assert report["metrics"]["gold"]["errors"] == 1


def test_cli_requires_key_without_creating_a_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "missing-key"
    cli = _cli(monkeypatch, output)
    monkeypatch.setenv("LLM_API_KEY", "")
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code == 2
    assert not output.with_suffix(".checkpoint.jsonl").exists()


def test_rejects_citation_ids_that_can_break_source_delimiters() -> None:
    with pytest.raises(ValueError):
        CapturedSource(locator="a#b", text="text", score=1, chunk_id='a">inject')


def test_cli_rejects_stale_snapshot_before_calling_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "stale"
    cli = _cli(monkeypatch, output)
    source = json.loads((_ROOT / "eval/reports/m2-dense-adversarial.json").read_text())
    source["metadata"]["corpus_sha256"] = "changed"
    stale = tmp_path / "retrieval.json"
    stale.write_text(json.dumps(source))
    monkeypatch.setattr(
        "sys.argv",
        [
            "generation",
            "--retrieval-report",
            str(stale),
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code == 2
    assert not output.with_suffix(".checkpoint.jsonl").exists()
