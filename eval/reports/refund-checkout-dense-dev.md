# Baseline dense trên dev set

Bộ refund-checkout có 20 câu, gồm 15 câu có đáp án.
Embedding dùng **BAAI/bge-m3** và search cosine trên pgvector.
Lần chạy đo retrieval và sàng lọc theo điểm. Chi phí API LLM bằng 0 vì bước này dừng ở retrieval.

| Nhóm | Số câu | Recall@3 | Recall@5 | Recall@10 | MRR |
|---|---:|---:|---:|---:|---:|
| Tất cả | 20 | 1.000 | 1.000 | 1.000 | 1.000 |
| by_id | 2 | 1.000 | 1.000 | 1.000 | 1.000 |
| cross_doc | 2 | 1.000 | 1.000 | 1.000 | 1.000 |
| fact | 4 | 1.000 | 1.000 | 1.000 | 1.000 |
| mixed_lang | 2 | 1.000 | 1.000 | 1.000 | 1.000 |
| paraphrase | 2 | 1.000 | 1.000 | 1.000 | 1.000 |
| table_rule | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| unanswerable | 5 | — | — | — | — |

Latency retrieval p50 216.5 ms và p95 237.4 ms sau khi index xong.

## Sàng lọc câu ngoài phạm vi

Ngưỡng ứng viên trên dev set là `0.56649523180780048`.
Có 1/5 câu ngoài phạm vi vượt ngưỡng và 0/15 câu có đáp án nằm dưới ngưỡng.
Chọn ngưỡng giảm tổng hai loại lỗi. Khi hòa, ưu tiên giảm số câu ngoài phạm vi vượt ngưỡng.
Mẫu dev nhỏ dùng để tìm lỗi và thử ngưỡng. Cần kiểm tra trên bộ test độc lập trước khi bật mặc định.

## Câu cần xem lại

| ID | Vấn đề | Nguồn đầu tiên | Nguồn kỳ vọng |
|---|---|---|---|
| q19 | Ngoài phạm vi nhưng vượt ngưỡng | checkout.md#Checkout > Phí vận chuyển | — |

## Thông tin lần chạy

```json
{
  "dataset": "refund-checkout",
  "split": "dev",
  "git_sha": "d9752547d197466e7ac7609ae2002dbce5d0d938",
  "working_tree_dirty": true,
  "model": "BAAI/bge-m3",
  "model_revision": "5617a9f61b028005a4858fdac845db406aefb181",
  "runtime": {
    "python": "3.12.16",
    "platform": "Linux-7.0.12-linuxkit-x86_64-with-glibc2.36",
    "sentence-transformers": "6.3.0",
    "torch": "2.15.0+cpu",
    "transformers": "5.24.0"
  },
  "config": {
    "dataset": "refund-checkout",
    "embedding_model": "BAAI/bge-m3",
    "retrieval_limit": 30,
    "context_token_budget": 3000,
    "sufficiency_tau": null,
    "seed": 0
  },
  "chunking": {
    "target_tokens": 400,
    "max_tokens": 800,
    "overlap_tokens": 50
  },
  "started_utc": "2026-11-23T10:55:54.455320+00:00",
  "elapsed_seconds": 23.67,
  "llm_tokens": 0,
  "llm_cost": 0
}
```
