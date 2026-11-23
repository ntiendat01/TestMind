# ADR 0002 — Phụ thuộc cho lát cắt Markdown

## Trạng thái

Chấp nhận.

## Bối cảnh

Lát cắt đầu của M1 lưu chunk Markdown vào Postgres/pgvector và gọi DeepSeek trên Forge. Chưa có parser Excel, lexical search, hay UI hỏi đáp.

## Quyết định

Thêm vào `apps/api`:

- `sqlalchemy`, `alembic`, `psycopg[binary]`, `pgvector` — schema và vector cosine
- `python-multipart` — FastAPI nhận file upload
- `httpx` — gọi `https://api.inference.wandb.ai/v1` (runtime, không chỉ dev)
- `sentence-transformers` — embedding local `BAAI/bge-m3`, nhóm optional `bge`

Image API cài extra `bge`. `make check` không tải model. Test tiêm embedder giả và không gọi Forge. Wheel PyTorch hiện không có cho macOS Intel; máy đó chạy embedding trong container Linux.

## Hệ quả

Image API nặng hơn vì có PyTorch. Lần embed đầu tải model về máy. Đổi model embedding thì phải reindex.
