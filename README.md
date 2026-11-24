# TestMind

Trợ lý truy xuất requirement và test case. API nhận `.md`, `.txt`, `.csv`, `.xlsx` và `.docx`, dùng embedding BGE-M3 local và trả câu trả lời có citation qua DeepSeek trên Forge.

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

`make check` gồm độ dài file, lint, typecheck và test.

Test tích hợp Markdown cần một cơ sở dữ liệu kiểm thử PostgreSQL có pgvector. Đặt
`TEST_DATABASE_URL` thành URL của cơ sở dữ liệu kiểm thử trước khi chạy `make test`.
Test tạo schema riêng, chạy Alembic và dọn schema sau khi chạy. Cơ sở dữ liệu kiểm thử
cần extension `vector` trong schema `public`. Nếu thiếu, runner sẽ cài và giữ extension
để các lần chạy dùng chung. Tài khoản cần quyền tạo schema và cài extension khi cần.

## Đo baseline dense

Đặt `TESTMIND_EVAL_DATABASE_URL` thành URL của cơ sở dữ liệu kiểm thử ở trên. Cài
embedding trên máy có wheel PyTorch tương thích bằng `cd apps/api && uv sync --extra bge`,
rồi chạy `make eval-dev` tại gốc repo. Báo cáo Markdown và JSON nằm trong `eval/reports/`.
`make smoke` dùng hash embedder và cùng database kiểm thử để kiểm tra việc nạp corpus và truy xuất.

Trên macOS Intel, có thể chạy evaluator bằng image API Linux đã build. Đặt
`EVAL_POSTGRES_URL` thành URL truy cập được từ network Compose, ví dụ dùng hostname
`postgres` với một database kiểm thử do bạn tạo.

```sh
docker compose run --rm --entrypoint /srv/.venv/bin/python \
  -e PYTHONPATH=/workspace/apps/api \
  -e TESTMIND_EVAL_DATABASE_URL="$EVAL_POSTGRES_URL" \
  -v "$PWD:/workspace:ro" -v "$PWD/eval/reports:/reports" \
  api /workspace/eval/cli.py dev --output /reports/dense-dev
```

Ngưỡng từ chối ứng viên được ghi trong báo cáo dev. Có thể cấu hình
`RETRIEVAL_MIN_SIMILARITY` để thử trên API. `make eval-test` cần bộ test độc lập
và `sufficiency_tau` cố định trong cấu hình trước khi chạy.

Dev set M2 có 60 câu nháp và bộ adversarial có 10 câu. Sau khi chạy dev, sao chép
cấu hình baseline và điền `sufficiency_tau` từ báo cáo để chạy
`make eval-adversarial CONFIG=config/exp/baseline_frozen.yaml`.
Runner ghi lịch sử trong schema `testmind_eval` của database kiểm thử, cần quyền
tạo schema và áp migration. Tệp `.review.jsonl` cạnh báo cáo dành cho QA kiểm tra
nhãn. Bộ test khóa và việc gán nhãn chéo cần người phụ trách dữ liệu hoàn tất.
