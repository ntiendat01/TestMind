"""Check metric denominators, score ties and fixed evaluation thresholds."""

import json
from math import log2
from pathlib import Path

from app.services.eval.metrics import (
    Observation,
    best_threshold,
    evaluate_threshold,
    mrr,
    ndcg_at,
    precision_at,
    recall_at,
    refusal_rates,
)
from app.services.eval.report import write_report


def test_metrics_use_gold_locators_and_skip_unanswerable_questions() -> None:
    observations = [
        Observation("a", "fact", True, frozenset({"one", "two"}), ("other", "one"), 0.8, 10),
        Observation("b", "unanswerable", False, frozenset(), ("one",), 0.3, 20),
    ]
    assert recall_at(observations, 1) == 0
    assert recall_at(observations, 3) == 0.5
    assert mrr(observations) == 0.5
    chosen = best_threshold(observations)
    assert 0.3 < chosen.minimum <= 0.8
    assert chosen.false_answers == chosen.over_refusals == 0


def test_fixed_threshold_is_not_tuned_on_holdout(tmp_path: Path) -> None:
    observations = [
        Observation("a", "fact", True, frozenset({"one"}), ("one",), 0.8, 10),
        Observation("b", "unanswerable", False, frozenset(), ("one",), 0.8, 20),
    ]
    assert best_threshold(observations).over_refusals == 1
    prefix = tmp_path / "dense"
    metadata = {"dataset": "fixture", "model": "fake", "split": "test"}
    write_report(prefix, observations, metadata, fixed_threshold=0.75)
    result = json.loads(prefix.with_suffix(".json").read_text())
    assert result["threshold_source"] == "fixed_config"
    assert result["threshold"] == {"minimum": 0.75, "false_answers": 1, "over_refusals": 0}


def test_precision_and_ndcg_do_not_credit_duplicate_sources() -> None:
    items = [Observation("a", "fact", True, frozenset({"a", "b"}), ("a", "a", "b"), 0.8, 1)]
    assert precision_at(items, 5) == 2 / 5
    assert ndcg_at(items, 3) == (1 + 0.5) / (1 + 1 / log2(3))
    assert refusal_rates(items, evaluate_threshold(items, 0.9)) == {
        "refusal_correct": None,
        "false_accept_rate": None,
        "over_refusal": 1.0,
    }
