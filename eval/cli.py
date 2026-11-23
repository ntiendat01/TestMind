"""Run the dense baseline against a disposable pgvector schema."""

import argparse
import os
import platform
import random
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from tempfile import TemporaryDirectory

from app.chunking.tokens import ApproximateTokenCounter
from app.clients.embedder import BgeM3Embedder, HashEmbedder
from app.core.interfaces import Embedder
from app.db.repositories.documents import PostgresDocumentStore
from app.db.workspace import migrated_workspace
from app.services.eval.report import write_report
from app.services.eval.runner import evaluate_dense, load_config, load_questions
from app.settings import Settings, discover_config_dir, load_chunk_config

_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split", choices=["dev", "test", "smoke"])
    parser.add_argument("--config", type=Path, default=Path("config/exp/baseline.yaml"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = load_config(_ROOT / args.config)
    dataset = _ROOT / "eval" / "datasets" / config.dataset
    split = "dev" if args.split == "smoke" else args.split
    question_path = dataset / f"{split}.jsonl"
    if not question_path.is_file():
        parser.error(f"Evaluation split does not exist: {question_path.relative_to(_ROOT)}")
    if args.split == "test" and config.sufficiency_tau is None:
        parser.error("Set a fixed sufficiency_tau in the config before evaluating the test set.")
    database_url = os.environ.get("TESTMIND_EVAL_DATABASE_URL") or os.environ.get(
        "TEST_DATABASE_URL"
    )
    if not database_url:
        parser.error("Set TESTMIND_EVAL_DATABASE_URL to a PostgreSQL test database with pgvector.")

    questions = load_questions(question_path)
    embedder: Embedder
    if args.split == "smoke":
        questions = [item for item in questions if item.answerable][:5] + [
            item for item in questions if not item.answerable
        ][:2]
        embedder = HashEmbedder()
    else:
        embedder = BgeM3Embedder(config.embedding_model)
    random.seed(config.seed)
    chunk_config = load_chunk_config(discover_config_dir())
    started = datetime.now(UTC)
    with (
        migrated_workspace(database_url) as sessions,
        TemporaryDirectory() as directory,
    ):
        items = evaluate_dense(
            questions=questions,
            corpus=dataset / "corpus",
            config=config,
            chunk_config=chunk_config,
            store=PostgresDocumentStore(sessions),
            embedder=embedder,
            counter=ApproximateTokenCounter(),
            raw_dir=Path(directory),
            max_upload_bytes=Settings().max_upload_bytes,
        )
    if args.split == "smoke":
        indexed_locators = {loc for item in items for loc in item.retrieved}
        missing_gold = {
            gold for item in items for gold in item.gold if gold not in indexed_locators
        }
        if not items or missing_gold:
            parser.error(f"Smoke retrieval did not find fixture locators: {sorted(missing_gold)}")
        print(f"eval smoke: indexed fixture and retrieved sources for {len(items)} questions.")
        return 0

    prefix = args.output or _ROOT / "eval" / "reports" / f"dense-{started:%Y%m%dT%H%M%SZ}"
    metadata = {
        "dataset": config.dataset,
        "split": split,
        "git_sha": os.environ.get("EVAL_GIT_SHA") or _git("rev-parse", "HEAD"),
        "working_tree_dirty": os.environ.get("EVAL_WORKING_TREE_DIRTY") == "1"
        if "EVAL_WORKING_TREE_DIRTY" in os.environ
        else bool(_git("status", "--porcelain")),
        "model": embedder.model_name,
        "model_revision": os.environ.get("EVAL_MODEL_REVISION"),
        "runtime": _runtime(),
        "config": config.model_dump(),
        "chunking": asdict(chunk_config),
        "started_utc": started.isoformat(),
        "elapsed_seconds": round((datetime.now(UTC) - started).total_seconds(), 3),
        "llm_tokens": 0,
        "llm_cost": 0,
    }
    write_report(prefix, items, metadata, config.sufficiency_tau if split == "test" else None)
    print(f"eval: wrote {prefix.with_suffix('.md')} and {prefix.with_suffix('.json')}.")
    return 0


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=_ROOT, check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _runtime() -> dict[str, str]:
    installed = {"python": platform.python_version(), "platform": platform.platform()}
    for package in ("sentence-transformers", "torch", "transformers"):
        try:
            installed[package] = version(package)
        except PackageNotFoundError:
            continue
    return installed


if __name__ == "__main__":
    raise SystemExit(main())
