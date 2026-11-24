"""Verify evidence binding, applicability, reviewer identities and agreement."""

import json
from pathlib import Path

import pytest
from app.services.eval.generation import GenerationObservation
from app.services.eval.review import ReviewScore, agreement, load_scores, summarize_reviews
from app.services.eval.review_packets import (
    ReviewCase,
    load_cases,
    observation_hash,
    read_cases,
    sample_cases,
    write_packets,
)

_ROOT = Path(__file__).resolve().parents[5]


def _case(refused: bool = False) -> ReviewCase:
    item = GenerationObservation("q1", "retrieved", "Question?", not refused, ["Point"], [])
    item.refused = refused
    return ReviewCase(
        case_id="dev:q1:retrieved",
        split="dev",
        source_run_id="run",
        source_report_sha256="report-hash",
        observation=item,
        observation_sha256=observation_hash(item),
    )


def _score(case: ReviewCase, **changes: object) -> dict[str, object]:
    return {
        "case_id": case.case_id,
        "observation_sha256": case.observation_sha256,
        "reviewer": "Alice",
        "reviewer_kind": "human",
        "faithfulness": 1,
        "answer_correctness": 1,
        "citation_support": 1,
        "label_accepted": True,
        "comments": "Verified against the supplied evidence.",
        **changes,
    }


def _write(path: Path, *rows: dict[str, object]) -> Path:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return path


def test_recovery_is_applied_before_reproducible_sampling(tmp_path: Path) -> None:
    reports = _ROOT / "eval/reports"
    cases = load_cases(
        [reports / "m2-generation-dev.json", reports / "m2-generation-adversarial.json"],
        [reports / "m2-generation-dev-recovery.json"],
    )
    assert len(cases) == 140
    assert not any(case.observation.error for case in cases)
    assert {case.observation.id for case in cases if case.recovered} == {"q34", "q38", "q48"}
    selected = sample_cases(cases, 40, 0)
    assert selected == sample_cases(cases, 40, 0)
    assert len(selected) == 80
    assert sum(case.split == "adversarial" for case in selected) == 20
    assert sum(case.recovered for case in selected) == 3
    prefix = tmp_path / "sample"
    write_packets(prefix, selected)
    assert read_cases(prefix.with_suffix(".cases.jsonl")) == selected
    with pytest.raises(ValueError, match="already exists"):
        write_packets(prefix, selected)


def test_recovery_cannot_silently_replace_a_different_run(tmp_path: Path) -> None:
    reports = _ROOT / "eval/reports"
    recovery = json.loads((reports / "m2-generation-dev-recovery.json").read_text())
    recovery["metadata"]["parent_report_sha256"] = "different"
    path = tmp_path / "recovery.json"
    path.write_text(json.dumps(recovery))
    with pytest.raises(ValueError, match="unchanged base"):
        load_cases([reports / "m2-generation-dev.json"], [path])


def test_pending_templates_have_no_human_metrics(tmp_path: Path) -> None:
    prefix = tmp_path / "sample"
    cases = [_case()]
    write_packets(prefix, cases)
    scores = load_scores([prefix.with_suffix(".reviewer-a.jsonl")], cases)
    result = summarize_reviews(cases, scores)
    assert result["human_reviewed_questions"] == 0
    assert result["human_agreement"] == []
    assert result["metrics"]["human"]["retrieved"]["faithfulness"]["mean"] is None


def test_agent_scores_are_not_counted_as_human_reviews(tmp_path: Path) -> None:
    case = _case()
    scores = load_scores(
        [
            _write(
                tmp_path / "agent.jsonl",
                _score(case, reviewer="Codex", reviewer_kind="agent"),
            )
        ],
        [case],
    )
    result = summarize_reviews([case], scores)
    assert result["human_reviewed_questions"] == 0
    assert result["metrics"]["agent"]["retrieved"]["answer_correctness"]["mean"] == 1


def test_duplicate_reviewer_and_changed_evidence_are_rejected(tmp_path: Path) -> None:
    case = _case()
    path = _write(tmp_path / "scores.jsonl", _score(case), _score(case))
    with pytest.raises(ValueError, match="Duplicate reviewer"):
        load_scores([path], [case])
    _write(path, _score(case, observation_sha256="changed"))
    with pytest.raises(ValueError, match="changed observation"):
        load_scores([path], [case])


def test_refusal_metrics_remain_not_applicable_and_partial_rows_are_visible(tmp_path: Path) -> None:
    case = _case(refused=True)
    path = _write(tmp_path / "scores.jsonl", _score(case))
    with pytest.raises(ValueError, match="Refusals have null"):
        load_scores([path], [case])
    _write(
        path,
        _score(
            case,
            faithfulness=None,
            citation_support=None,
            answer_correctness=None,
        ),
    )
    result = summarize_reviews([case], load_scores([path], [case]))
    assert result["human_started_questions"] == 1
    assert result["human_reviewed_questions"] == 0


@pytest.mark.parametrize("value", [True, 0.7, -1, "1"])
def test_ordinal_scores_reject_invalid_inputs(value: object) -> None:
    with pytest.raises(ValueError):
        ReviewScore.model_validate(_score(_case(), faithfulness=value))


def test_cohen_kappa_uses_shared_nonmissing_labels() -> None:
    measured = agreement([(1, 1), (1, 0), (0.5, 0.5), (0, 0)])
    assert measured["agreement"] == 0.75
    assert measured["cohen_kappa"] == pytest.approx(7 / 11)
    assert agreement([(1, 1)])["cohen_kappa"] is None
    assert agreement([])["agreement"] is None


def test_two_humans_share_one_case_mean_and_agreement(tmp_path: Path) -> None:
    case = _case()
    path = _write(
        tmp_path / "two-reviewers.jsonl",
        _score(case),
        _score(case, reviewer="Bob", faithfulness=0.5),
    )
    result = summarize_reviews([case], load_scores([path], [case]))
    assert result["human_reviewed_questions"] == 1
    assert result["metrics"]["human"]["retrieved"]["faithfulness"] == {
        "mean": 0.75,
        "cases": 1,
    }
    measured = next(item for item in result["human_agreement"] if item["metric"] == "faithfulness")
    assert measured["pairs"] == 1
    assert measured["agreement"] == 0
