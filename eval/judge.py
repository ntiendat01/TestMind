"""Run model judging on a review packet without disclosing existing reviewer scores."""

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.clients.llm import InferenceLLMClient
from app.services.eval.judge import JudgeResult, evaluate_judge
from app.services.eval.judge_report import write_judge_report
from app.services.eval.review import load_scores
from app.services.eval.review_packets import read_cases
from app.services.generation.prompt import load_prompt
from app.settings import Settings, discover_config_dir

_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--compare", type=Path, nargs="*", default=[])
    parser.add_argument("--context", choices=["retrieved", "gold", "both"], default="retrieved")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--model")
    parser.add_argument("--max-tokens", type=int, default=1600)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    all_cases = read_cases(args.cases)
    references = load_scores(args.compare, all_cases)
    cases = [
        case
        for case in all_cases
        if (args.context == "both" or case.observation.context == args.context)
    ]
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive.")
        cases = cases[: args.limit]
    if not cases or args.max_tokens < 1:
        parser.error("Select at least one case and a positive max token limit.")
    settings = Settings(_env_file=_ROOT / ".env")
    if not settings.llm_api_key:
        parser.error("Set LLM_API_KEY before calling the judge.")
    model = args.model or settings.llm_model
    prompt_path = discover_config_dir() / "prompts/judge_generation.vi.md"
    version, system = load_prompt(prompt_path)
    started = datetime.now(UTC)
    run_id = str(uuid4())
    reviewer = f"judge:{model}:{version}:{run_id}"
    prefix = args.output or _ROOT / "eval/reports" / f"judge-{run_id}"
    prefix.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".scores.jsonl", ".checkpoint.jsonl", ".json", ".md"):
        if prefix.with_suffix(suffix).exists():
            parser.error("Output exists. Choose a fresh prefix.")
    client = InferenceLLMClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=model,
        max_tokens=args.max_tokens,
        timeout=settings.llm_timeout_seconds,
    )
    results: list[JudgeResult] = []
    failures = 0
    with prefix.with_suffix(".checkpoint.jsonl").open("x", encoding="utf-8") as checkpoint:
        for case in cases:
            result = evaluate_judge(case, client, system=system, reviewer=reviewer)
            results.append(result)
            payload = asdict(result)
            payload["score"] = result.score.model_dump() if result.score else None
            checkpoint.write(json.dumps(payload, ensure_ascii=False) + "\n")
            checkpoint.flush()
            print(f"judge {case.case_id}: {result.error or 'complete'}", flush=True)
            failures = (
                failures + 1
                if result.error
                in {
                    "llm_unavailable",
                    "llm_transport_error",
                    "llm_not_configured",
                }
                else 0
            )
            if failures >= 3:
                break
    metadata = {
        "run_id": run_id,
        "reviewer": reviewer,
        "model": model,
        "prompt_version": version,
        "prompt_sha256": hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "comparison_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in args.compare
        },
        "context": args.context,
        "max_tokens": args.max_tokens,
        "temperature": 0,
        "planned_cases": len(cases),
        "attempted_cases": len(results),
        "complete": len(results) == len(cases) and not any(item.error for item in results),
        "tokens_in": sum(item.tokens_in for item in results),
        "tokens_out": sum(item.tokens_out for item in results),
        "cost": None,
        "started_utc": started.isoformat(),
        "elapsed_seconds": (datetime.now(UTC) - started).total_seconds(),
        "git_sha": _git("rev-parse", "HEAD"),
        "working_tree_dirty": bool(_git("status", "--porcelain")),
    }
    write_judge_report(prefix, all_cases, results, references, metadata)
    print(f"Judge report saved to {prefix.with_suffix('.md')}")
    return int(any(item.error for item in results))


def _git(*args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=_ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


if __name__ == "__main__":
    raise SystemExit(main())
