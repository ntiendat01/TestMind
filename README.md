# TestMind

Trợ lý truy xuất requirement và test case. Khung M0 chạy được ba service và kiểm tra sức khỏe API. Chưa có ingestion, hỏi đáp, hay số đo.

## Chạy local

```bash
docker compose up --build
```

- Web: <http://localhost:3000>
- API: <http://localhost:8000/v1/health>
- Postgres: `localhost:5432`, user/password/db mặc định `testmind` (xem `.env.example`)

## Kiểm tra

```bash
make check
```

`make check` gồm độ dài file, lint, typecheck và test. Eval và benchmark chưa có số liệu (`TBD` cho tới M2/M3).
