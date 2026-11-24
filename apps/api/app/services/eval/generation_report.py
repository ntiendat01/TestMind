"""Write paired generation metrics and editable human-review records."""

import json
from dataclasses import asdict
from pathlib import Path
from statistics import median, quantiles

from app.services.eval.generation import GenerationObservation, generation_metrics


def write_generation_report(
    prefix: Path,
    items: list[GenerationObservation],
    metadata: dict[str, object],
) -> dict[str, object]:
    metrics = {
        variant: generation_metrics([item for item in items if item.context == variant])
        for variant in ("retrieved", "gold")
    }
    report: dict[str, object] = {
        "metadata": metadata,
        "metrics": metrics,
        "metrics_by_type": {
            variant: {
                kind: generation_metrics(
                    [item for item in items if item.context == variant and item.kind == kind]
                )
                for kind in sorted({item.kind for item in items})
            }
            for variant in ("retrieved", "gold")
        },
        "observations": [asdict(item) for item in items],
    }
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    prefix.with_suffix(".review.jsonl").write_text(
        "".join(
            json.dumps(
                asdict(item)
                | {
                    "reviewer": None,
                    "faithfulness": None,
                    "answer_correctness": None,
                    "citation_support": None,
                    "injection_followed": None,
                    "comments": None,
                },
                ensure_ascii=False,
            )
            + "\n"
            for item in items
        ),
        encoding="utf-8",
    )
    rows = [
        "# Đánh giá generation và citation",
        "",
        f"Model {metadata.get('model')}. Run {metadata.get('run_id')}.",
        f"Số lượt dự kiến {metadata.get('planned_samples', len(items))}, "
        f"đã thử {len(items)}, hoàn tất {metadata.get('complete', False)}.",
        "Mỗi câu chạy hai lần với prompt chung, một lần dùng context truy xuất đã lưu "
        "và một lần dùng nguồn gold. Cả hai lượt bỏ qua cổng ngưỡng retrieval để đo riêng LLM.",
        "Với câu không có đáp án, gold context rỗng. Ý đáp án kỳ vọng chỉ xuất trong tệp review.",
        "Citation validity kiểm tra membership trên citation thô trước bộ lọc backend. "
        "Citation support, faithfulness, correctness và việc làm theo injection chờ QA chấm.",
        "Lỗi API hoặc JSON được đếm riêng và loại khỏi mẫu số tỷ lệ đáp án. "
        "Chi phí để TBD khi chưa có giá provider được xác minh.",
        "",
        "| Context | Mẫu | Lỗi | Từ chối đúng | Trả lời ngoài phạm vi | Từ chối nhầm "
        "| Citation validity | Answer citation coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    latency_rows = []
    for variant, measured in metrics.items():
        values = [
            measured[key]
            for key in (
                "samples",
                "errors",
                "refusal_correct",
                "false_answer_rate",
                "over_refusal",
                "citation_validity",
                "answer_citation_coverage",
            )
        ]
        rows.append(f"| {variant} | " + " | ".join(_format(value) for value in values) + " |")
        latency_rows.append(
            f"{variant} token vào {measured['tokens_in']}, token ra {measured['tokens_out']}. "
            "Chi phí TBD."
        )
        completed = [
            item.latency_ms for item in items if item.context == variant and not item.error
        ]
        if completed:
            p95 = (
                quantiles(completed, n=20, method="inclusive")[-1]
                if len(completed) > 1
                else completed[0]
            )
            latency_rows.append(
                f"{variant} latency p50 {median(completed):.1f} ms, p95 {p95:.1f} ms."
            )
    rows.extend(["", *latency_rows])
    rows.extend(
        [
            "",
            "## Câu cần xem lại",
            "",
            "| ID | Context | Vấn đề tự động phát hiện |",
            "|---|---|---|",
        ]
    )
    for item in items:
        problems = []
        if item.error:
            problems.append(item.error)
        elif item.refused == item.answerable:
            problems.append("Từ chối nhầm" if item.answerable else "Trả lời ngoài phạm vi")
        if item.citations_valid < item.citations_total:
            problems.append("Citation ngoài context")
        if item.refused is False and (
            item.claims_total == 0 or item.claims_total != item.claims_cited
        ):
            problems.append("Câu trả lời thiếu nguồn")
        if problems:
            rows.append(f"| {item.id} | {item.context} | {', '.join(problems)} |")
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
    return report


def _format(value: float | int | None) -> str:
    if value is None:
        return "TBD"
    return str(value) if isinstance(value, int) else f"{value:.3f}"
