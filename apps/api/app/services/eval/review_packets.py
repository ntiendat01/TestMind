"""Build reproducible review samples and apply verified recovery results."""

import hashlib
import json
import random
from pathlib import Path

from app.services.eval.generation import GenerationObservation
from pydantic import BaseModel, TypeAdapter


class ReviewCase(BaseModel):
    case_id: str
    split: str
    source_run_id: str
    source_report_sha256: str
    recovered: bool = False
    observation_sha256: str
    observation: GenerationObservation


def observation_hash(item: GenerationObservation) -> str:
    data = TypeAdapter(GenerationObservation).dump_json(item)
    return hashlib.sha256(data).hexdigest()


def load_cases(reports: list[Path], recoveries: list[Path]) -> list[ReviewCase]:
    runs = {}
    cases: dict[str, ReviewCase] = {}
    for path in reports:
        report = json.loads(path.read_text(encoding="utf-8"))
        metadata = report["metadata"]
        run_id = metadata["run_id"]
        if run_id in runs:
            raise ValueError("Base run IDs must be unique.")
        runs[run_id] = (metadata, hashlib.sha256(path.read_bytes()).hexdigest())
        for raw in report["observations"]:
            case = _case(raw, metadata, path, recovered=False)
            if case.case_id in cases:
                raise ValueError(f"Duplicate review case {case.case_id}.")
            cases[case.case_id] = case
    for path in recoveries:
        report = json.loads(path.read_text(encoding="utf-8"))
        metadata = report["metadata"]
        parent = runs.get(metadata.get("parent_run_id"))
        if parent is None or parent[1] != metadata.get("parent_report_sha256"):
            raise ValueError("Recovery must refer to an unchanged base report.")
        for key in (
            "dataset",
            "split",
            "corpus_sha256",
            "dataset_sha256",
            "prompt_sha256",
            "model",
        ):
            if metadata.get(key) != parent[0].get(key):
                raise ValueError(f"Recovery differs from base metadata: {key}.")
        for raw in report["observations"]:
            case = _case(raw, metadata, path, recovered=True)
            previous = cases.get(case.case_id)
            if previous is None or not previous.observation.error or case.observation.error:
                raise ValueError("Recovery may replace only a failed matching case with a success.")
            if previous.observation.question != case.observation.question:
                raise ValueError("Recovery question differs from base question.")
            if previous.observation.sources != case.observation.sources:
                raise ValueError("Recovery context differs from base context.")
            cases[case.case_id] = case
    return sorted(cases.values(), key=lambda case: case.case_id)


def _case(
    raw: dict[str, object],
    metadata: dict[str, object],
    path: Path,
    *,
    recovered: bool,
) -> ReviewCase:
    item = TypeAdapter(GenerationObservation).validate_python(raw)
    split = str(metadata["split"])
    if split not in {"dev", "adversarial"}:
        raise ValueError("Prepare review packets from dev or adversarial runs.")
    return ReviewCase(
        case_id=f"{split}:{item.id}:{item.context}",
        split=split,
        source_run_id=str(metadata["run_id"]),
        source_report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        recovered=recovered,
        observation_sha256=observation_hash(item),
        observation=item,
    )


def sample_cases(cases: list[ReviewCase], count: int, seed: int) -> list[ReviewCase]:
    by_question: dict[tuple[str, str], list[ReviewCase]] = {}
    for case in cases:
        by_question.setdefault((case.split, case.observation.id), []).append(case)
    if not 1 <= count <= len(by_question):
        raise ValueError("Sample size must be positive and no larger than the question pool.")
    selected = {
        key
        for key, items in by_question.items()
        if key[0] == "adversarial" or any(item.recovered for item in items)
    }
    if len(selected) > count:
        raise ValueError("Sample is too small to retain all adversarial and recovered questions.")
    groups: dict[tuple[str, str, bool], list[tuple[str, str]]] = {}
    for key, items in by_question.items():
        if key not in selected:
            item = items[0].observation
            groups.setdefault((key[0], item.kind, item.answerable), []).append(key)
    rng = random.Random(seed)
    for group in groups.values():
        rng.shuffle(group)
    while len(selected) < count:
        for group_key in sorted(groups):
            if groups[group_key] and len(selected) < count:
                selected.add(groups[group_key].pop())
    return [case for case in cases if (case.split, case.observation.id) in selected]


def write_packets(prefix: Path, cases: list[ReviewCase]) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = [
        prefix.with_suffix(suffix)
        for suffix in (
            ".cases.jsonl",
            ".reviewer-a.jsonl",
            ".reviewer-b.jsonl",
        )
    ]
    if any(path.exists() for path in paths):
        raise ValueError("Review packet already exists. Choose a new output prefix.")
    paths[0].write_text(
        "".join(case.model_dump_json() + "\n" for case in cases),
        encoding="utf-8",
    )
    for path in paths[1:]:
        path.write_text(
            "".join(
                json.dumps(
                    {
                        "case_id": case.case_id,
                        "observation_sha256": case.observation_sha256,
                        "reviewer": "",
                        "reviewer_kind": "human",
                        "faithfulness": None,
                        "answer_correctness": None,
                        "citation_support": None,
                        "injection_followed": None,
                        "label_accepted": None,
                        "comments": "",
                    },
                    ensure_ascii=False,
                )
                + "\n"
                for case in cases
            ),
            encoding="utf-8",
        )


def read_cases(path: Path) -> list[ReviewCase]:
    cases = [
        ReviewCase.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    if len({case.case_id for case in cases}) != len(cases) or not cases:
        raise ValueError("Case IDs must be unique and packet must be nonempty.")
    if any(case.observation_sha256 != observation_hash(case.observation) for case in cases):
        raise ValueError("Review packet observation digest does not match its content.")
    return cases
