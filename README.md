# TestMind

Trợ lý truy xuất requirement và test case. Khung M0 chạy ba service. Lát cắt Markdown nhận file `.md`/`.txt`, embed local BGE-M3, và trả câu trả lời có citation qua DeepSeek trên Forge.

## Chạy local

```bash
docker compose up --build
```

- Web: <http://localhost:3000>
- API: <http://localhost:8000/v1/health>
- Postgres: `localhost:5432`, user/password/db mặc định `testmind` (xem `.env.example`)

Đặt `LLM_API_KEY` trong `.env` (không commit) trước khi hỏi đáp. Model mặc định là `deepseek-ai/DeepSeek-V4.1-Flash-1017` trên `https://api.inference.wandb.ai/v1`. Lần embed đầu trong container tải `BAAI/bge-m3`.

## Kiểm tra

```bash
make check
```

`make check` gồm độ dài file, lint, typecheck và test. Eval và benchmark chưa có số liệu (`TBD` cho tới M2/M3).
