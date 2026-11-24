# Roadmap & Milestones

Ước lượng giả định làm part-time, chỉ mang tính tham khảo thô; điều chỉnh theo thực tế sau M1.

## M0 — Scaffold (2–4 ngày)
**Deliverables:** monorepo (`apps/web`, `apps/api`, `crates/tm-core`, `eval`, `docs`, `bench`), Docker Compose
(web, api, postgres+pgvector), `Makefile` (`check`, `test`, `eval-dev`, `reindex`), CI GitHub Actions,
script `scripts/check_file_length.py` (fail nếu file > 500 dòng, chỉ miễn lockfile + file `AUTO-GENERATED`), `.env.example`,
health check, sinh OpenAPI client.
**Acceptance:** `docker compose up` chạy 3 service; `make check` xanh trên repo rỗng; CI chạy được.
**Rủi ro:** toolchain Rust/maturin trong Docker; dành thời gian nhưng chưa viết logic Rust.

## M1 — Ingestion + Basic RAG, end-to-end (1.5–2.5 tuần)
**Deliverables:** upload DOCX/MD/XLSX/CSV; parser **Python tham chiếu**; structure-aware chunking; embedding BGE-M3;
pgvector; Q&A có citation + từ chối; Next.js `/documents` + `/chat` (SSE, Source panel); dataset giả lập v1.
**Acceptance:** demo end-to-end; upload lại cùng file không trùng chunk; citation mở đúng vị trí; câu ngoài phạm vi bị từ chối.
**Rủi ro:** parse Excel/bảng; UI nuốt thời gian; dataset yếu.
**Phụ thuộc:** `docs/specs/01-ingestion.md`, `docs/specs/02-retrieval.md` (dense), `docs/specs/03-generation-citation.md`, `docs/specs/06-frontend.md`.

## M2 — Evaluation Harness (1–1.5 tuần) ← làm sớm, trước khi tối ưu

Tiến độ kỹ thuật cập nhật ngày 24/11/2026. Đã có 60 câu dev nháp, 10 câu đối kháng, metric retrieval, quét ngưỡng, báo cáo lỗi và lịch sử `eval_runs`. Runner generation chạy context retrieved/gold đã có kiểm thử bằng fake client, chờ API key để đo model thật. Các nhãn chờ QA duyệt và gán chéo. Test holdout khóa cùng đánh giá faithfulness, correctness và citation_support còn cần hoàn thiện trước khi nghiệm thu M2.

**Deliverables:** `eval/` runner, dev/test split, 60–100 câu (có unanswerable + adversarial),
metric (bản Python), báo cáo Markdown, bảng `eval_runs`, baseline đo thật.
**Acceptance:** `make eval-dev` ra bảng baseline với số thật; có danh sách câu thất bại.
**Rủi ro:** ground truth kém chất lượng (rủi ro lớn nhất của dự án) → nhờ ít nhất một người thứ hai gán nhãn một mẫu.

## M3 — Advanced Retrieval + Rust core (2–3 tuần)
**Deliverables:** lexical BM25 (Python tham chiếu → **tantivy**), hybrid RRF, metadata filter, ID lookup,
(tuỳ chọn) reranker; thí nghiệm E1–E8; port các module Rust (`lexical`, `parse_xlsx/csv/md`, `chunk`, `fusion`, `metrics`)
với golden test; `bench/` Python vs Rust (E9).
**Acceptance:** bảng so sánh E1–E9 với số thật; module Rust nào không cải thiện đo được thì ghi ADR giữ Python.
**Rủi ro:** tokenizer tiếng Việt; reranker không có lợi (kết quả hợp lệ); đồng bộ tantivy↔Postgres.

## M4 — QA Traceability (2–3 tuần)
**Deliverables:** `requirements`/`test_cases` extraction + column mapping UI; trace candidates + LLM-judge có kiểm tra evidence;
coverage 4 nhãn (gợi ý); xác nhận/bác bỏ; ma trận + CSV; ground truth `trace_gt`; metric trace.
**Acceptance:** báo cáo Recall/nDCG ứng viên và Precision nhãn theo `explicit`/`semantic`; UI `/trace` dùng được.
**Rủi ro:** mapping sai trình bày như chắc chắn → luôn kèm evidence + review.

## M5 — Production-oriented (1.5–2.5 tuần)
**Deliverables:** similar-bug retrieval (nếu còn thời gian), rate limit/quota/cache, structured logging,
test E2E Playwright, error handling/retry, deploy Docker Compose lên VM/free-tier, README + sơ đồ + ADR + video demo ngắn,
trang phân tích lỗi + báo cáo benchmark cuối.
**Acceptance:** CI xanh (lint/type/test/file-length/smoke eval); dựng lại từ README; có demo chạy được.
**Rủi ro:** over-engineering; chi phí API (đặt ngân sách ngày + cache).

## Cắt scope khi trễ tiến độ (ưu tiên giữ → bỏ)
1. M1, M2 (nền tảng + đo) — **không cắt**.
2. Hybrid + filter + ID lookup (M3).
3. Traceability explicit + semantic candidates (M4) — bỏ LLM-judge nếu thiếu thời gian.
4. Rust: giữ `lexical` + `metrics`; bỏ các module còn lại.
5. Similar-bug, test-case recommendation, eval UI — làm sau.

## 5 quyết định cần chốt sớm
1. Domain dataset: **refund/checkout**. Schema Excel mẫu vẫn để lúc làm parser bảng.
2. Cấu hình chunking: giả thuyết `target_tokens=400`, `max_tokens=800`, `overlap_tokens=50`. Excel: 1 chunk mỗi dòng. Chưa tune.
3. Embedding: **local BGE-M3** (`BAAI/bge-m3`, 1024 chiều).
4. LLM: **DeepSeek-V4.1-Flash** tại `https://api.inference.wandb.ai/v1`, model `deepseek-ai/DeepSeek-V4.1-Flash-1017`. Ngân sách ngày chưa đặt số.
5. Cách gán và kiểm tra ground truth (ai gán, bao nhiêu mẫu gán đôi). Chưa chốt; thuộc M2.

## Chi phí & triển khai (cần xác minh giá hiện tại)
- Embedding: local BGE-M3 (không tốn tiền API; tốn CPU/RAM). Nếu dùng API, cần kiểm tra bảng giá.
- LLM: chi phí chính; dùng model rẻ cho eval hàng loạt, cache, `max_tokens`, ngân sách ngày.
- DB/hosting: Postgres + pgvector tự host trong Compose; free-tier của nền tảng hosting thay đổi liên tục → kiểm tra trước khi chọn.
- Demo công khai: chỉ dữ liệu mẫu, tắt upload tuỳ ý, rate limit.
