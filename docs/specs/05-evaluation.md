# Spec 05 — Evaluation Framework

## Nguyên tắc
- Đo trước, tối ưu sau. Mọi kỹ thuật "advanced" phải thắng baseline **trên số đo**, nếu không thì bỏ.
- Không bịa số liệu. Bảng kết quả trong docs để `TBD` cho tới khi có lần chạy thật.
- Dev set để tune; **test set khóa** chỉ chạy khi chốt cấu hình.

## Dataset

Cấu trúc:
```
eval/datasets/<domain>/
  corpus/            # BRD, test case xlsx, bug csv (giả lập/công khai, ghi nguồn + giấy phép)
  dev.jsonl          # để tune
  test.jsonl         # KHÓA - không sửa, không dùng để tune
  adversarial.jsonl  # prompt injection, mâu thuẫn, ngoài phạm vi
  trace_gt.jsonl     # ground truth req -> test cases
  bug_gt.jsonl       # ground truth bug trùng
  README.md          # cách tạo, nguồn, giới hạn
```

Một dòng câu hỏi:
```json
{
  "id": "q_017", "type": "table_rule", "lang": "vi",
  "question": "...",
  "gold_chunks": ["<locator ổn định>"],
  "gold_answer_points": ["ý 1", "ý 2"],
  "answerable": true
}
```
- `gold_chunks` dùng **locator ổn định** (doc + section_path/row), không dùng chunk_id (đổi khi đổi chunking).
  Runner ánh xạ locator → chunk theo cấu hình chunking hiện tại (chunk "chứa" locator là chunk đúng).
- Câu hỏi `answerable=false` là bắt buộc (tối thiểu ~15–20% bộ).

Phân loại `type`: `fact`, `by_id`, `paraphrase`, `table_rule`, `multi_hop`, `cross_doc`,
`conflict_version`, `unanswerable`, `mixed_lang`. Số lượng MVP: **60–100 câu**, mỗi nhóm đủ để đọc được
(báo cáo theo nhóm, không chỉ trung bình). Nêu rõ giới hạn thống kê của bộ nhỏ.

Quy tắc chống leakage: câu hỏi viết lại, không copy nguyên văn; không dùng LLM đang đánh giá để sinh toàn bộ
câu hỏi mà không duyệt tay; test set tách file, không đi vào prompt/few-shot; gán nhãn bởi ≥2 người cho một
mẫu để đo đồng thuận.

## Metric

| Tầng | Metric | Ghi chú |
|---|---|---|
| Retrieval | Recall@{3,5,10}, MRR, nDCG@10 (khi có độ liên quan nhiều bậc), Precision@K | Tính trong `tm_core::metrics` (bản Python đối chiếu) |
| Từ chối | Refusal đúng (câu unanswerable), False-answer rate, Over-refusal (câu answerable bị từ chối) | Báo cả hai chiều |
| Generation | Faithfulness (claim được context ủng hộ), Answer correctness (so `gold_answer_points`) | LLM-judge + **chấm tay mẫu ≥30–50 câu** để đo đồng thuận |
| Citation | `citation_validity` (tự động), `citation_support` (chấm tay/judge) | |
| Hệ thống | Latency p50/p95 từng bước, tokens, cost/100 câu | |
| Trace | Recall@K/nDCG@K ứng viên; Precision nhãn sau judge; theo `explicit`/`semantic` | Spec 04 |
| Bug | Recall@K bug trùng, MRR | Phase 2 |

Retrieval và generation **đánh giá riêng**: generation còn chạy với *gold context* để tách lỗi do retrieval.

Khoảng tin cậy: bootstrap (ví dụ 1000 lần) cho các chênh lệch giữa cấu hình; chênh lệch trong khoảng nhiễu
không được ghi là "cải thiện".

## Thí nghiệm bắt buộc (bảng so sánh)

| ID | So sánh |
|---|---|
| E1 | Fixed-size chunk vs structure-aware chunk |
| E2 | Có/không prefix section_path khi embed |
| E3 | BM25 vs Dense vs Hybrid (RRF) |
| E4 | Có/không metadata filter, ID lookup |
| E5 | Có/không reranker (kèm latency, cost) |
| E6 | Tokenizer lexical: syllable vs bigram; có/không bỏ dấu |
| E7 | Embedding model A vs B (ví dụ BGE-M3 vs model khác) |
| E8 | Ngưỡng sufficiency τ (đường Refusal vs Over-refusal) |
| E9 | Python vs Rust cho lexical/parse (chất lượng không đổi, tốc độ đo ở `bench/`) |

## Runner & lưu kết quả

- Baseline dense đầu tiên dùng dev set giả lập refund/checkout, đo Recall@3/5/10, MRR, latency retrieval và ngưỡng từ chối. `config/exp/baseline.yaml` dùng cú pháp JSON tương thích YAML.
- Runner chạy migration trong schema tạm, giữ Markdown và JSON trong `eval/reports/`. Smoke dùng hash embedder. Test độc lập đọc ngưỡng cố định từ `sufficiency_tau`.
- CLI: `make eval-dev CONFIG=config/exp/baseline.yaml`, `make eval-test` (chỉ khi chốt).
- Mỗi run lưu vào `eval_runs` + `eval/reports/<run_id>.md`: git SHA, config snapshot, model/version, prompt_version,
  seed, thời gian, tokens, cost, metric tổng + theo nhóm, danh sách câu **thất bại** (phân tích lỗi).
- Chạy tất định: seed cố định, `temperature=0` cho generation/judge.
- **Regression gate**: CI chạy eval nhỏ (smoke, ~10 câu, LLM giả hoặc cache) để bắt lỗi pipeline;
  eval đầy đủ chạy thủ công.

## Bảng kết quả (điền sau khi đo thật)

| Cấu hình | Recall@5 | MRR | nDCG@10 | Faithfulness | Citation valid | Refusal đúng | Over-refusal | p50/p95 (ms) | Cost/100q |
|---|---|---|---|---|---|---|---|---|---|
| Baseline (fixed + dense) | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| + structure-aware | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| + hybrid | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| + filter/ID lookup | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| + reranker | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Acceptance
- `make eval-dev` chạy một lệnh, sinh báo cáo Markdown có bảng trên với số thật.
- Có trang phân tích lỗi liệt kê ≥10 câu thất bại kèm nguyên nhân (retrieval/generation/data).
