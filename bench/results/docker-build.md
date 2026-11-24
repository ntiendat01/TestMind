# Đo Docker build ngày 24/11/2026

Số liệu lấy từ log BuildKit trên máy hiện tại. Thay đổi theo ADR 0006, dựa trên commit
`3f8e1169d5e6350f4ef784b01f5f0cd7cbc98136`, working tree có thay đổi chưa commit.
Docker Desktop dùng Linux amd64, 8 CPU, RAM VM 8.322.801.664 byte, Engine 29.7.2,
Compose 5.5.1. Mỗi kịch bản đo một lần, chưa đánh giá biến thiên.

## Kết quả

| Kịch bản | Trước | Sau |
|---|---|---|
| API, thời gian trong build history | 9 phút 35 giây | 2 phút 45 giây |
| API, bước cài dependency | 282,9 giây | 60,2 giây |
| API, bước export và unpack image | 290,4 giây | 96,5 giây |
| API, kích thước do `docker image ls` báo | 9,28 GB | 1,79 GB |
| Web, thời gian trong build history | 2 phút 47 giây | 2 phút 54 giây |
| Web, riêng bước `pnpm build` | 159,9 giây | 95,0 giây |
| Build cả hai service, wall clock lần đầu sau thay đổi | Chưa đo | 176,774 giây |
| Build cả hai service, không đổi source, cache đã có | Chưa đo | 6,527 giây |
| Sửa một file Python, rebuild API | Chưa đo | 4,295 giây |
| Sửa một file CSS, rebuild web | Chưa đo | 69,058 giây |

Build API/web chạy song song. Build đầu sau thay đổi có cache mount uv, pnpm và Next.js
ban đầu rỗng. Web trước thay đổi có dependency layer cache sẵn, còn lần đầu sau thay đổi
phải chạy lại pnpm install, mất 58,2 giây. Vì vậy tổng thời gian web đầu tiên chưa giảm.
Sau sửa CSS, dependency layer dùng cache và riêng bước `pnpm build` mất 57,0 giây.

Hai phép đo sửa source thực hiện trong bản sao tạm bằng cách thêm comment, dùng tag
`testmind-api:cache-smoke` và `testmind-web:cache-smoke`. Source thật và container đang chạy
không bị sửa hoặc khởi động lại. Các bước uv sync/pnpm install đều CACHED khi sửa source.

## Cách đo

Đọc baseline từ lịch sử Docker có sẵn, không chạy lại bản CUDA nặng chỉ để đo.
ID build và dữ liệu tổng hợp nằm trong [docker-build.json](docker-build.json).

```sh
docker buildx history inspect yznc8ij4zuszs9extdy8xdv1j
docker buildx history logs yznc8ij4zuszs9extdy8xdv1j
docker compose --progress plain build api web
docker compose --progress plain build api web
docker image ls --filter reference=testmind-api --format '{{.Size}}'
```

Wall clock được đo bằng `time.monotonic()` bao quanh process Docker. Thời gian từng bước
lấy từ dòng DONE của BuildKit. Kích thước `image ls` và trường `image inspect .Size`
được ghi riêng trong JSON, không dùng lẫn hai cách báo kích thước để tính mức giảm.

## Kiểm tra

- `make check` qua, gồm 71 test API, 12 test web và 2 test script. Hai test database
  được bỏ qua vì chưa đặt `TEST_DATABASE_URL`.
- `scripts/test_api_image.py` chạy trong image không có mạng, cả ba test qua. Torch có
  hậu tố `+cpu`, phép nhân tensor đúng, không cài NVIDIA/CUDA/Triton. Import được
  sentence-transformers và API. Cache uv và `.env` không nằm trong image.
- Container web thử nghiệm không có mạng trả HTTP 200 cho `/documents`, `/chat`, `/eval`.
- `docker compose config --quiet` qua.

## Giới hạn

Đây là số đo một máy và một lần chạy cho mỗi kịch bản, không phải thời gian bảo đảm.
Lần không đổi source chỉ chứng minh layer cache được dùng lại. Thay đổi dependency,
base image hoặc builder, mạng chậm hay cache bị dọn có thể làm build lâu hơn.
Chưa đo tải model BGE-M3 hoặc tốc độ embedding. Cache model nằm trong volume riêng
và lần dùng đầu vẫn cần tải. Không đổi model, prompt hoặc thuật toán retrieval trong task này.

Khi sửa UI, dùng `pnpm dev` để có Fast Refresh. Build production vẫn cần cho kiểm tra
đóng gói và trước khi triển khai. Lệnh thường dùng nằm trong README.
