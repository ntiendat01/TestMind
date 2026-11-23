# Spec 01 — Document Ingestion

## Mục tiêu
Biến file upload thành các `chunk` có cấu trúc, có metadata và citation location chính xác;
cập nhật/xoá không gây trùng lặp.

## Định dạng hỗ trợ

| Định dạng | MVP | Parser | Ghi chú |
|---|---|---|---|
| `.md`, `.txt` | ✅ | Python (M1). Rust `parse::md` ở M3 | Heading tree |
| `.docx` | ✅ | Python `python-docx` (Rust hoãn) | Heading, đoạn, bảng |
| `.xlsx`, `.csv` | ✅ | Python `openpyxl` / `csv` (M1). Rust ở M3 | Mỗi dòng = một record |
| `.pdf` (có text) | Phase 2 | Python (`pymupdf`) | Không OCR |
| PDF scan | ❌ | — | Ngoài scope |

Giới hạn: kích thước ≤ 20 MB/file (cấu hình được), kiểm tra MIME + đuôi file.

## Mô hình trung gian: `ParsedDocument`

Parser (Python hoặc Rust) đều trả cùng cấu trúc (JSON schema ở `docs/specs/07-rust-core.md`):

```
ParsedDocument
  doc_type, language_hint
  blocks[]: Block
Block
  kind: heading | paragraph | table | list_item | row
  text, level (heading), section_path ["3 Thanh toán", "3.2 Hoàn tiền"]
  loc: {page?, sheet?, row?, col_range?, paragraph_idx?}
  table?: {header[], rows[][]}
  fields?: {col_name: value}   # cho row của Excel
```

## Chunking (structure-aware)

| Nguồn | Đơn vị chunk | Quy tắc |
|---|---|---|
| Văn bản (BRD/SRS/process) | Section (theo heading) | Gộp đoạn trong cùng section tới `target_tokens`; vượt `max_tokens` thì tách theo đoạn, **overlap** nhỏ; không cắt giữa bảng hoặc giữa một requirement có ID |
| Bảng business rule | **1 chunk/bảng** nếu nhỏ; bảng lớn tách theo nhóm dòng, **lặp lại header** ở mỗi chunk | Render dạng `cột: giá trị` để embed tốt |
| Test case (Excel) | **1 chunk/test case** (1 dòng) | Text gồm `tc_key, title, steps, expected, linked_req`; metadata giữ riêng |
| Bug report | 1 chunk/bug | Gồm title, repro, actual, expected |
| Requirement có ID (`REQ-\d+`) | Nhận diện bằng regex cấu hình được | Điền `requirement_ids` cho chunk |

Tham số mặc định (trong `config/chunking.yaml`, **phải tune trên dev set, không chốt cảm tính**):
`target_tokens=400`, `max_tokens=800`, `overlap_tokens=50`.

`text_for_embedding` = `"{doc_name} > {section_path}\n{text}"` (prefix ngữ cảnh). Đây là giả thuyết cần A/B, không mặc định đúng.

## Chunk ID & idempotency

`chunk.id = sha1(version_id | canonical_loc | ordinal)`.
- Upload cùng `content_hash` → bỏ qua, trả version hiện có.
- Upload version mới của cùng `document` → version mới `is_active=true`, version cũ `is_active=false`
  (hoặc xoá theo cấu hình `retention`). Truy vấn mặc định chỉ thấy `is_active`.
- Toàn bộ upsert trong **một transaction**; lỗi giữa chừng → rollback, version `status=failed` kèm `error`.
- Xoá document: xoá chunk, vector, entry tantivy, file gốc.

## Trích xuất có cấu trúc (cho traceability)

- Từ BRD: tạo bản ghi `requirements` khi nhận diện được ID (regex) hoặc heading dạng yêu cầu. Nếu không có ID,
  sinh `req_key` ổn định từ `section_path` và đánh dấu `auto_key=true`.
- Từ Excel test case: ánh xạ cột bằng **column mapping** (cấu hình theo file; UI cho phép chọn cột):
  `tc_key, title, steps, expected, linked_req, module, priority, status`. Cột thiếu → null, không đoán.
- Từ Excel/CSV bug: tương tự với `bug_key, title, repro, actual, expected, module, env, status`.

## Trạng thái job

`job_id` là `document_versions.id`.

`queued → parsing → chunking → embedding → indexing → ready` hoặc `failed`. Lưu `progress` (0–100) và `error`.

Lát cắt Markdown xử lý đồng bộ trong request. Client nhận `202`, rồi `GET /v1/jobs/{id}` thấy `ready` hoặc `failed`. Định dạng khác Markdown trả `400` cho tới khi parser của định dạng đó có mặt.

## Embedding

- Batch (ví dụ 32), retry có giới hạn, cache theo `sha1(text_for_embedding)` để không embed lại khi nội dung chunk không đổi.
- Lưu `model_name` + `model_version` cùng vector; đổi model → cần reindex (lệnh `make reindex`).

## Test bắt buộc

- Upload cùng file 2 lần → số chunk không đổi.
- Upload version mới → chunk cũ `is_active=false`, truy vấn không trả chunk cũ.
- Bảng nhiều dòng → mỗi chunk con có header.
- Excel có cột thiếu/ô trống/ô gộp → không crash, ghi cảnh báo.
- File sai định dạng/quá lớn → lỗi 4xx rõ ràng.
- So sánh Rust và Python trên cùng fixture là cổng của M3. M1 kiểm tra parser Python.

## Acceptance
- Ingest bộ dataset mẫu end-to-end không lỗi; mỗi chunk có `section_path`/`loc` đủ để mở lại nguồn gốc.
- Citation location của 100% chunk trong fixture trỏ đúng vị trí (kiểm tra tự động trên fixture).
