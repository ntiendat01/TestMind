# ADR 0006 — PyTorch CPU và cache Docker

## Trạng thái

Chấp nhận.

## Bối cảnh

Build API ngày 24/11/2026 mất 9 phút 35 giây. Log Docker ghi 282,9 giây ở bước
`uv sync` và 290,4 giây xuất image. PyTorch mặc định từ PyPI trên Linux kéo thêm
NVIDIA/CUDA và Triton. Image được Docker báo 9,28 GB, riêng layer cài gói là 5,91 GB.
Dockerfile chưa dùng cache mount nên cache uv cũng nằm trong layer dependency.

Dự án dùng BGE-M3 local trên CPU. Frontend cũng thiếu cache pnpm/Next.js qua các lần build.

## Quyết định

- Khai báo rõ torch trong extra `bge`, trỏ nguồn Linux tới index CPU chính thức của PyTorch
  với `explicit=true`. Các gói khác vẫn từ PyPI. Giữ lockfile và cài bằng `--frozen`.
  Torch đã có gián tiếp qua sentence-transformers, không thêm thư viện hay đổi model embedding.
- Dùng BuildKit cache mount cho uv, pnpm và `.next/cache`. Cache tải gói không đi vào image API.
  Stage build web kế thừa stage dependency để tránh sao chép lại node_modules và chuẩn bị pnpm hai lần.
- Loại `.env`, cache máy local và tệp sinh khỏi build context.
- Giữ cache model Hugging Face trong volume `api_models`, dùng `HF_HOME=/srv/models`.
  Tạo lại container vẫn dùng cache model đã tải. Lần đầu còn cần tải model.
- Build production theo service đã sửa. Khi chỉ khởi động lại, dùng `docker compose up -d`
  để dùng image sẵn có. Cache không thay thế bước build khi đã sửa source.

## Hệ quả

Image Linux mặc định phục vụ CPU. Triển khai GPU cần quyết định và cấu hình index riêng.
Cache Docker thuộc builder hiện tại, không tự chuyển sang máy khác hoặc CI runner mới.
Không dùng `--no-cache` hoặc prune cache thường xuyên khi phát triển.

Số đo sau thay đổi và điều kiện đo được ghi trong `bench/results/docker-build.md`.

## Nguồn

- [uv với PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/)
- [uv trong Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [Docker build cache](https://docs.docker.com/build/cache/optimize/)
- [Next.js build cache](https://nextjs.org/docs/app/guides/ci-build-caching)
