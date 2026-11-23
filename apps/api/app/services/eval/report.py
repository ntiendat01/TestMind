"""Render a dense dev run with subgroup metrics, failure details and provenance."""

import json
from dataclasses import asdict
from pathlib import Path
from statistics import median, quantiles

from app.services.eval.metrics import (
    Observation,
    Threshold,
    best_threshold,
    evaluate_threshold,
    mrr,
    recall_at,
)


def write_report(
    prefix: Path,
    items: list[Observation],
    metadata: dict[str, object],
    fixed_threshold: float | None,
) -> None:
    threshold = (
        best_threshold(items)
        if fixed_threshold is None
        else evaluate_threshold(items, fixed_threshold)
    )
    output = {
        "metadata": metadata,
        "observations": [asdict(item) | {"gold": sorted(item.gold)} for item in items],
        "metrics": _metrics(items),
        "latency_ms": _latency(items),
        "threshold": asdict(threshold),
        "threshold_source": "dev_sweep" if fixed_threshold is None else "fixed_config",
    }
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".json").write_text(
        json.dumps(output, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    prefix.with_suffix(".md").write_text(
        _markdown(items, metadata, threshold, fixed_threshold is None), encoding="utf-8"
    )


def _metrics(items: list[Observation]) -> dict[str, float | None]:
    return {f"recall@{k}": recall_at(items, k) for k in (3, 5, 10)} | {"mrr": mrr(items)}


def _latency(items: list[Observation]) -> dict[str, float]:
    latencies = [item.latency_ms for item in items]
    p95 = quantiles(latencies, n=20, method="inclusive")[-1] if len(items) > 1 else latencies[0]
    return {"p50": median(latencies), "p95": p95}


def _markdown(
    items: list[Observation], metadata: dict[str, object], threshold: Threshold, swept: bool
) -> str:
    latency = _latency(items)
    answerable = sum(item.answerable for item in items)
    rows = [
        f"# Baseline dense trên {metadata['split']} set",
        "",
        f"Bộ {metadata['dataset']} có {len(items)} câu, gồm {answerable} câu có đáp án.",
        f"Embedding dùng **{metadata['model']}** và search cosine trên pgvector.",
        "Lần chạy đo retrieval và sàng lọc theo điểm. "
        "Chi phí API LLM bằng 0 vì bước này dừng ở retrieval.",
        "",
        "| Nhóm | Số câu | Recall@3 | Recall@5 | Recall@10 | MRR |",
        "|---|---:|---:|---:|---:|---:|",
        _metric_row("Tất cả", items),
    ]
    for kind in sorted({item.kind for item in items}):
        rows.append(_metric_row(kind, [item for item in items if item.kind == kind]))
    rows.extend(
        [
            "",
            f"Latency retrieval p50 {latency['p50']:.1f} ms và p95 {latency['p95']:.1f} ms "
            "sau khi index xong.",
            "",
            "## Sàng lọc câu ngoài phạm vi",
            "",
            f"{'Ngưỡng ứng viên trên dev set' if swept else 'Ngưỡng cố định trong cấu hình'} "
            f"là `{threshold.minimum:.17g}`.",
            f"Có {threshold.false_answers}/{len(items) - answerable} câu ngoài phạm vi vượt ngưỡng "
            f"và {threshold.over_refusals}/{answerable} câu có đáp án nằm dưới ngưỡng.",
        ]
    )
    if swept:
        rows.extend(
            [
                "Chọn ngưỡng giảm tổng hai loại lỗi. "
                "Khi hòa, ưu tiên giảm số câu ngoài phạm vi vượt ngưỡng.",
                "Mẫu dev nhỏ dùng để tìm lỗi và thử ngưỡng. "
                "Cần kiểm tra trên bộ test độc lập trước khi bật mặc định.",
            ]
        )
    rows.extend(
        [
            "",
            "## Câu cần xem lại",
            "",
            "| ID | Vấn đề | Nguồn đầu tiên | Nguồn kỳ vọng |",
            "|---|---|---|---|",
        ]
    )
    rows.extend(_failure_rows(items, threshold.minimum))
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
    return "\n".join(rows)


def _metric_row(label: str, items: list[Observation]) -> str:
    cells = " | ".join(
        f"{value:.3f}" if value is not None else "—" for value in _metrics(items).values()
    )
    return f"| {label} | {len(items)} | {cells} |"


def _failure_rows(items: list[Observation], minimum: float) -> list[str]:
    rows = []
    for item in items:
        passed = item.top_score is not None and item.top_score >= minimum
        reasons = []
        if passed and not item.answerable:
            reasons.append("Ngoài phạm vi nhưng vượt ngưỡng")
        if not passed and item.answerable:
            reasons.append("Có đáp án nhưng dưới ngưỡng")
        if item.answerable and not item.gold.issubset(item.retrieved[:3]):
            reasons.append("Thiếu nguồn chuẩn trong top 3")
        if reasons:
            top = item.retrieved[0] if item.retrieved else "—"
            gold = ", ".join(sorted(item.gold)) or "—"
            rows.append(f"| {item.id} | {', '.join(reasons)} | {top} | {gold} |")
    return rows or ["| — | Không thấy lỗi theo các điều kiện trên | — | — |"]
