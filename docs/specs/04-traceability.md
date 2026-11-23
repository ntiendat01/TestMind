# Spec 04 — Requirement–Test Traceability (điểm nhấn QA)

## Nguyên tắc
- Đầu ra là **ứng viên + bằng chứng + điểm**, KHÔNG phải kết luận. Con người xác nhận.
- Không bao giờ dùng semantic similarity một mình để tuyên bố "đã kiểm thử đầy đủ".
- Liên kết tường minh (ID) luôn có độ tin cậy cao hơn liên kết ngữ nghĩa.

## Đầu vào
`requirements` (từ BRD/SRS) và `test_cases` (từ Excel), đã ingest theo spec 01.

## Thuật toán mapping cho một requirement R

1. **Explicit links**: test case có `linked_req_keys` chứa `R.req_key` → `source=explicit`, điểm cố định cao.
   Liên kết trỏ tới key không tồn tại → ghi nhận `dangling_link` (một phát hiện hữu ích cho QA).
2. **Candidate retrieval** (`source=semantic`): dùng retrieval (spec 02) giới hạn `doc_types=[testcase]`,
   query = `R.title + R.text`, top-N (mặc định 15), cùng `module` nếu có.
3. **Chấm liên quan** cho top-M (mặc định 5) ứng viên chưa explicit, bằng LLM-judge có cấu trúc:
   - Đầu vào: văn bản requirement + một test case.
   - Đầu ra JSON: `label ∈ {covers, partial, unrelated}`, `evidence_req` (trích nguyên văn từ requirement),
     `evidence_tc` (trích từ test case), `reason` ngắn.
   - Backend kiểm tra: hai đoạn `evidence_*` **phải là chuỗi con** của văn bản gốc; sai → hạ về `unrelated`/`unverified`.
4. Lưu `trace_links` với `review_state=pending`. Người dùng xác nhận/bác bỏ → lưu lại (nguồn ground truth cho eval).

Chi phí: LLM chỉ gọi cho top-M; có cache theo `(req_hash, tc_hash, prompt_version)`.

## Trạng thái coverage (gợi ý, không phải sự thật)

| Nhãn hiển thị | Điều kiện heuristic | Ghi chú UI |
|---|---|---|
| **Chưa thấy test liên quan** | Không có explicit link và không có ứng viên `covers/partial` | Có thể do mapping sót; cho phép tìm thủ công |
| **Có test liên quan** | ≥1 link `explicit` hoặc `covers` đã xác minh evidence | KHÔNG đồng nghĩa "đủ" |
| **Nghi ngờ thiếu scenario** | Có link nhưng chỉ `partial`, hoặc requirement có điều kiện/ngoại lệ/ngưỡng không thấy trong test | Hiển thị lý do + đoạn requirement liên quan |
| **Requirement chưa đủ rõ** | Heuristic: thiếu điều kiện chấp nhận, từ mơ hồ ("nhanh", "phù hợp"), mâu thuẫn giữa nguồn | Gắn cờ để BA làm rõ |

Mọi nhãn đi kèm cảnh báo "gợi ý tự động". Việc đếm (số test/requirement, tỷ lệ) làm bằng SQL, không dùng LLM.

## Gợi ý test case còn thiếu (Phase 2, ưu tiên thấp)

- Chỉ sinh cho requirement ở trạng thái "Nghi ngờ thiếu scenario".
- Mỗi test đề xuất bắt buộc có `source_quote` (trích nguyên văn requirement) — backend kiểm tra là chuỗi con.
- Test không có căn cứ phải đánh dấu `assumption=true` và hiển thị rõ là giả định.
- Kỹ thuật gợi ý: boundary, negative, state transition, từ chính điều kiện đã nêu trong requirement.

## Similar bug retrieval (Phase 2)

Điểm kết hợp: semantic (title+repro+actual) + lexical (mã lỗi, message, endpoint) + khớp `module/component`,
`env/version`, `status`. Trọng số cấu hình được; tune trên dev set. Hiển thị lý do khớp từng yếu tố.
**Không** làm Bug-vs-Not-a-Bug trong MVP; nếu sau này làm: chỉ trả business rule liên quan + nhãn
`supported/contradicted/insufficient`, mặc định `insufficient`.

## API

- `POST /v1/trace/requirements/{key}` → danh sách link `{test_case, source, score, label, evidence, review_state}`.
- `POST /v1/trace/run` → chạy cho toàn bộ requirement của một document version (job nền).
- `PATCH /v1/trace/links/{id}` → `{review_state: confirmed|rejected}`.
- `GET /v1/trace/matrix` → ma trận requirement × test case (cho UI), kèm bộ lọc theo nhãn.
- Xuất CSV ma trận (QA thường cần).

## Test bắt buộc

- Explicit link đúng → luôn xuất hiện, không cần LLM.
- Link trỏ key không tồn tại → `dangling_link`.
- `evidence_req` không phải chuỗi con requirement → bị loại.
- Cache hoạt động (lần chạy 2 không gọi LLM với cặp không đổi).
- Requirement không test nào → nhãn "Chưa thấy test liên quan".

## Acceptance
- Trên dataset giả lập có ground truth mapping: báo cáo nDCG@K/Recall@K của ứng viên (trước khi LLM-judge)
  và Precision của nhãn sau judge, theo từng nguồn (`explicit` vs `semantic`).
