# ADR 0001 — Gói phụ thuộc cho khung M0

## Trạng thái

Chấp nhận.

## Bối cảnh

`docs/architecture.md` mục 2 đã chốt Next.js, FastAPI, PostgreSQL 16 + pgvector và Docker Compose. M0 cần các gói cụ thể để ba service khởi động và `make check` chạy được. Chưa có parser, retrieval, embedding, LLM hay binding Rust.

## Quyết định

API (`apps/api`, Python 3.12, uv):

- `fastapi`, `uvicorn` — process HTTP và OpenAPI
- `pydantic-settings` — đọc biến môi trường
- `ruff`, `mypy`, `pytest`, `httpx` — lint, type, test (dev)

Web (`apps/web`):

- `next`, `react`, `react-dom`, `typescript`, `eslint`, `eslint-config-next`
- `tailwindcss`, `postcss`, `autoprefixer` — Tailwind có mặt từ khung, đúng spec 06
- `openapi-typescript` — `scripts/gen_api_client.sh` sinh type từ OpenAPI (dev)

Postgres dùng image `pgvector/pgvector:pg16`. Chưa thêm driver SQLAlchemy/Alembic cho tới migration đầu tiên.

## Chưa đưa vào M0

- `shadcn/ui`: cài cùng component UI đầu tiên (M1)
- PyO3, maturin, tantivy: M3. Image `api` hiện chỉ chạy Python
- LangChain, LlamaIndex: không dùng

## Hệ quả

Thêm gói ngoài danh sách này cần một ADR mới.
