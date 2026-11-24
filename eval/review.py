"""Prepare review packets and summarize validated human or agent scores."""

import argparse
import json
from pathlib import Path

from app.services.eval.review import load_scores, summarize_reviews
from app.services.eval.review_packets import load_cases, read_cases, sample_cases, write_packets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--report", type=Path, action="append", required=True)
    prepare.add_argument("--recovery", type=Path, action="append", default=[])
    prepare.add_argument("--count", type=int, default=40)
    prepare.add_argument("--seed", type=int, default=0)
    prepare.add_argument("--output", type=Path, required=True)
    summary = commands.add_parser("summarize")
    summary.add_argument("--cases", type=Path, required=True)
    summary.add_argument("--scores", type=Path, nargs="+", required=True)
    summary.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            selected = sample_cases(load_cases(args.report, args.recovery), args.count, args.seed)
            write_packets(args.output, selected)
            print(f"Prepared {len(selected)} contexts for {args.count} questions.")
        else:
            cases = read_cases(args.cases)
            result = summarize_reviews(cases, load_scores(args.scores, cases))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(f"Summary saved to {args.output}")
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
