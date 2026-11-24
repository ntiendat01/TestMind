"""Evaluate production generation using a measured retrieval snapshot and oracle context."""

import argparse
import hashlib
import json
import os
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.clients.llm import InferenceLLMClient
from app.db.repositories.eval_runs import save_run
from app.schemas.parsed import ChunkConfig
from app.services.eval.contexts import (
    RetrievalSnapshot,
    corpus_hash,
    gold_inventory,
    paired_contexts,
)
from app.services.eval.generation import GenerationObservation, evaluate_answer
from app.services.eval.generation_report import write_generation_report
from app.services.eval.runner import load_questions
from app.settings import Settings, discover_config_dir, load_answer_prompt

_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieval-report", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    snapshot_path = args.retrieval_report.resolve()
    snapshot = RetrievalSnapshot.model_validate_json(snapshot_path.read_text(encoding="utf-8"))
    dataset_name = str(snapshot.metadata["dataset"])
    split = str(snapshot.metadata["split"])
    if split not in {"dev", "adversarial", "test"} or Path(dataset_name).name != dataset_name:
        parser.error("Snapshot must reference a supported split and one dataset directory.")
    dataset = _ROOT / "eval" / "datasets" / dataset_name
    questions_path = dataset / f"{split}.jsonl"
    if (
        hashlib.sha256(questions_path.read_bytes()).hexdigest()
        != snapshot.metadata["dataset_sha256"]
    ):
        parser.error("Dataset hash differs from the retrieval snapshot. Run retrieval again.")
    if corpus_hash(dataset / "corpus") != snapshot.metadata["corpus_sha256"]:
        parser.error("Corpus hash differs from the retrieval snapshot. Run retrieval again.")
    chunking = snapshot.metadata["chunking"]
    if not isinstance(chunking, dict):
        parser.error("Snapshot needs a chunking configuration.")
    config = ChunkConfig(**chunking)
    questions = load_questions(questions_path)
    contexts = paired_contexts(questions, snapshot, gold_inventory(dataset / "corpus", config))
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive.")
        contexts = contexts[: args.limit * 2]

    settings = Settings(_env_file=_ROOT / ".env")
    if not settings.llm_api_key:
        parser.error(
            "Set LLM_API_KEY in the environment or root .env before generation evaluation."
        )
    client = InferenceLLMClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout_seconds,
    )
    prompt_path = discover_config_dir() / "prompts" / "answer.vi.md"
    prompt_version, prompt = load_answer_prompt(discover_config_dir())
    started = datetime.now(UTC)
    run_id = str(uuid4())
    prefix = args.output or _ROOT / "eval" / "reports" / f"generation-{run_id}"
    prefix.parent.mkdir(parents=True, exist_ok=True)
    items: list[GenerationObservation] = []
    provider_failures = 0
    checkpoint = prefix.with_suffix(".checkpoint.jsonl")
    with checkpoint.open("x", encoding="utf-8") as stream:
        for question, variant, hits in contexts:
            item = evaluate_answer(
                question,
                variant,
                hits,
                client,
                system=prompt,
                prompt_version=prompt_version,
            )
            items.append(item)
            stream.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
            stream.flush()
            print(f"generation {question.id} {variant}: {item.error or 'complete'}", flush=True)
            provider_failures = (
                provider_failures + 1
                if item.error in {"llm_transport_error", "llm_unavailable", "llm_not_configured"}
                else 0
            )
            if provider_failures >= 3:
                break
    metadata = {
        "run_id": run_id,
        "dataset": dataset_name,
        "split": split,
        "mode": "generation",
        "model": settings.llm_model,
        "prompt_version": prompt_version,
        "prompt_sha256": hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
        "retrieval_report_sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
        "retrieval_run_id": snapshot.metadata.get("run_id"),
        "dataset_sha256": snapshot.metadata["dataset_sha256"],
        "corpus_sha256": snapshot.metadata["corpus_sha256"],
        "labels_status": snapshot.metadata.get("labels_status"),
        "git_sha": _git("rev-parse", "HEAD"),
        "working_tree_dirty": bool(_git("status", "--porcelain")),
        "started_utc": started.isoformat(),
        "elapsed_seconds": (datetime.now(UTC) - started).total_seconds(),
        "config": {"temperature": 0, "max_tokens": settings.llm_max_tokens, "limit": args.limit},
        "planned_samples": len(contexts),
        "attempted_samples": len(items),
        "complete": len(items) == len(contexts) and not any(item.error for item in items),
    }
    report = write_generation_report(prefix, items, metadata)
    database = os.environ.get("TESTMIND_EVAL_DATABASE_URL") or os.environ.get("TEST_DATABASE_URL")
    if database:
        save_run(database, report)
    print(f"generation report: {prefix.with_suffix('.md')}")
    return int(any(item.error for item in items))


def _git(*args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=_ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


if __name__ == "__main__":
    raise SystemExit(main())
