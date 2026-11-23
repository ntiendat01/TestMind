# ADR 0003 — Phụ thuộc cho trang Tài liệu và Hỏi đáp

## Trạng thái

Chấp nhận.

## Bối cảnh

Spec 06 yêu cầu Next.js gọi API, TanStack Query, và chuỗi tiếng Việt tập trung. Lát cắt này chỉ có `/documents` và `/chat`. Chưa có trace, eval, hay ánh xạ cột Excel.

## Quyết định

- `@tanstack/react-query` — cache danh sách tài liệu và trạng thái job
- `vitest` — test parser SSE
- Thành phần nút, ô nhập, bảng nằm trong `components/ui` bằng Tailwind. shadcn/Radix được thêm khi có dialog hoặc menu thật.

## Hệ quả

Web chỉ gọi `NEXT_PUBLIC_API_URL` (mặc định `http://localhost:8000`). API cho phép origin `WEB_ORIGIN`.
