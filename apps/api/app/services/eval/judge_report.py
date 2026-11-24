"""Report model-judge scores and case-level disagreements with other reviewers."""

import json
from dataclasses import asdict
from pathlib import Path

from app.services.eval.judge import JudgeResult
from app.services.eval.review import ReviewScore, agreement, summarize_reviews
from app.services.eval.review_packets import ReviewCase

_METRICS = (
    "faithfulness",
    "answer_correctness",
    "citation_support",
    "injection_followed",
    "label_accepted",
)


def compare_scores(
    judges: list[ReviewScore],
    references: list[ReviewScore],
) -> dict[str, list[dict[str, object]]]:
    by_case = {score.case_id: score for score in judges}
    if len(by_case) != len(judges):
        raise ValueError("Judge scores must have unique case IDs.")
    comparisons = []
    differences = []
    for reviewer in sorted({score.reviewer for score in references}):
        rows = [score for score in references if score.reviewer == reviewer]
        for metric in _METRICS:
            pairs = []
            for reference in rows:
                judged = by_case.get(reference.case_id)
                if judged is None:
                    continue
                if judged.observation_sha256 != reference.observation_sha256:
                    raise ValueError("Comparison scores must refer to the same observation.")
                a, b = getattr(reference, metric), getattr(judged, metric)
                if a is None or b is None:
                    continue
                pairs.append((a, b))
                if a != b:
                    differences.append(
                        {
                            "case_id": reference.case_id,
                            "metric": metric,
                            "reference": a,
                            "judge": b,
                            "reference_reviewer": reference.reviewer,
                            "reference_kind": reference.reviewer_kind,
                            "reference_comments": reference.comments,
                            "judge_comments": judged.comments,
                        }
                    )
            comparisons.append(
                {
                    "reference_reviewer": reviewer,
                    "reference_kind": rows[0].reviewer_kind,
                    "metric": metric,
                    **agreement(pairs),
                }
            )
    return {"agreement": comparisons, "disagreements": differences}


def write_judge_report(
    prefix: Path,
    cases: list[ReviewCase],
    results: list[JudgeResult],
    references: list[ReviewScore],
    metadata: dict[str, object],
) -> dict[str, object]:
    scores = [item.score for item in results if item.score is not None]
    comparison = compare_scores(scores, references)
    output: dict[str, object] = {
        "metadata": metadata,
        "summary": summarize_reviews(cases, scores),
        "comparison": comparison,
        "results": [
            asdict(item)
            | {
                "score": item.score.model_dump() if item.score else None,
            }
            for item in results
        ],
    }
    prefix.with_suffix(".scores.jsonl").write_text(
        "".join(score.model_dump_json() + "\n" for score in scores),
        encoding="utf-8",
    )
    prefix.with_suffix(".json").write_text(
        json.dumps(output, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    rows = [
        "# Đối chiếu LLM judge",
        "",
        f"Model {metadata['model']}. Prompt {metadata['prompt_version']}.",
        f"Đã thử {len(results)} case; có {len(scores)} điểm hợp lệ.",
        "Đây là điểm model, cần đối chiếu với người QA trước khi dùng để nghiệm thu.",
        "Nếu judge và generator dùng cùng model, kết quả có nguy cơ thiên lệch tự đánh giá.",
        "",
        "| Reviewer đối chiếu | Loại | Tiêu chí | Số cặp | Đồng ý | Cohen kappa |",
        "|---|---|---|---:|---:|---:|",
    ]
    for item in comparison["agreement"]:
        rows.append(
            f"| {item['reference_reviewer']} | {item['reference_kind']} | {item['metric']} "
            f"| {item['pairs']} | {_format(item['agreement'])} | {_format(item['cohen_kappa'])} |"
        )
    rows.extend(
        [
            "",
            "## Trường hợp bất đồng",
            "",
            "| Case | Tiêu chí | Điểm trước | Judge | Nhận xét judge |",
            "|---|---|---:|---:|---|",
        ]
    )
    for item in comparison["disagreements"]:
        comment = str(item["judge_comments"]).replace("|", "\\|").replace("\n", " ")
        rows.append(
            f"| {item['case_id']} | {item['metric']} | {item['reference']} "
            f"| {item['judge']} | {comment} |"
        )
    for result in results:
        if result.error:
            rows.append(f"| {result.case_id} | Lỗi {result.error} | — | — | — |")
    rows.extend(
        [
            "",
            "## Thông tin lần chạy",
            "",
            "```json",
            json.dumps(metadata, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    prefix.with_suffix(".md").write_text("\n".join(rows), encoding="utf-8")
    return output


def _format(value: object) -> str:
    return f"{value:.3f}" if isinstance(value, (int, float)) else "TBD"
