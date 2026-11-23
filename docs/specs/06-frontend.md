# Spec 06 — Frontend (Next.js)

## Stack
Next.js (App Router) + TypeScript strict + Tailwind + shadcn/ui + TanStack Query.
API client sinh từ OpenAPI (`openapi-typescript` + `openapi-fetch`). `pnpm gen:api` gọi `scripts/gen_api_client.sh`.
UI mặc định tiếng Việt, chuỗi tập trung trong `lib/i18n/vi.ts` (dễ thêm tiếng Anh).

## Nguyên tắc
- Frontend **không chứa logic RAG**, không giữ API key LLM. Chỉ gọi `apps/api`.
- Phần lớn trang là Client Component có TanStack Query; dùng Server Component cho layout/tĩnh.
- Mọi call API đi qua `lib/api/`; không `fetch` trong component.
- Component < 150 dòng; file < 500 dòng (luật cứng trong `AGENT.md` ở gốc repo).

## Cấu trúc thư mục

```
apps/web/
  app/
    (app)/documents/page.tsx
    (app)/chat/page.tsx
    (app)/trace/page.tsx
    (app)/eval/page.tsx
    (app)/history/page.tsx
    layout.tsx
  components/
    documents/ chat/ trace/ eval/ ui/
  lib/
    api/        # client sinh + wrapper
    sse/        # parse SSE
    i18n/
  hooks/
```

## Trang & chức năng

### /documents
- Upload (drag & drop), chọn `doc_type`, `module`.
- Với Excel: bước **chọn ánh xạ cột** (xem preview 5 dòng đầu) trước khi ingest.
- Bảng tài liệu: tên, loại, version, trạng thái job (polling `GET /v1/jobs/{id}`), số chunk, hành động (xoá, upload version mới).
- Hiển thị lỗi ingestion rõ ràng.

### /chat
- Ô hỏi + bộ lọc (loại tài liệu, module).
- Streaming câu trả lời qua SSE (`retrieval` → `token` → `final` → `usage`), có nút huỷ.
- Câu trả lời hiển thị claim kèm **chip citation** `[1][2]`; hover xem trích đoạn; click mở **Source panel**
  (document, section_path, loc: trang/sheet/dòng, đoạn gốc được highlight).
- Claim `unverified` hiển thị cảnh báo. Trạng thái `insufficient_evidence` hiển thị lý do + nguồn gần nhất.
- Hiển thị latency/token/cost của lượt hỏi (collapsible).

### /trace
- Danh sách requirement (lọc theo nhãn coverage, module).
- Chi tiết requirement: đoạn gốc, các test case ứng viên (`source`, điểm, nhãn, evidence hai phía), nút **Xác nhận/Bác bỏ**.
- Ma trận requirement × test case; xuất CSV.
- Cảnh báo cố định: "Gợi ý tự động, cần QA xác nhận".
- Hiển thị `dangling_link`.

### /eval
- Danh sách `eval_runs` (config, thời gian, metric chính).
- So sánh hai run (bảng chênh lệch + cảnh báo nếu trong khoảng nhiễu).
- Xem danh sách câu thất bại của một run.
- (MVP) có thể chỉ đọc báo cáo do CLI sinh; nút chạy eval từ UI để Phase 3.

### /history
- Lịch sử truy vấn (câu hỏi, thời gian, latency, cost), mở lại kết quả.

## Trạng thái & lỗi
- Skeleton khi tải; empty state có hướng dẫn (chưa có tài liệu → CTA upload).
- Lỗi API hiển thị `error.code` + thông điệp thân thiện; không lộ stack trace.
- Quota/rate limit (429) hiển thị thông báo thử lại sau.

## Accessibility & hiệu năng
- Điều hướng bàn phím cho Source panel; tương phản đủ; có dark mode (shadcn).
- Danh sách dài (requirement, chunk) dùng virtualization khi > ~200 dòng.

## Test
- Unit: hook SSE (chuỗi sự kiện, huỷ, lỗi giữa chừng), mapping citation.
- Component: Source panel, bảng trace, upload flow (Vitest + Testing Library).
- E2E tối thiểu (Playwright): upload → hỏi → thấy citation → mở nguồn. Chạy với API dùng LLM giả.

## Acceptance
- Demo hoàn chỉnh luồng: upload BRD + test case → hỏi đáp có citation → xem trace → xác nhận một link.
- `pnpm lint`, `pnpm typecheck`, `pnpm test` xanh; không `any`.
