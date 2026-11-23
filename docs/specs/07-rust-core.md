# Spec 07 — Rust Core (`crates/tm-core`)

## Vai trò
Thư viện Rust biên dịch thành Python extension (PyO3 + maturin), gọi **in-process** từ FastAPI.
Chỉ chứa tính toán thuần (CPU-bound, không mạng, không DB, không LLM).

## Vì sao in-process (PyO3) thay vì service riêng
- Không thêm hop mạng/serialization; một image, một tiến trình, dễ deploy.
- Giữ được ranh giới sạch nhờ interface rõ ràng. Nếu sau này cần tách, interface giữ nguyên.
- Đánh đổi: panic/lỗi Rust phải được chuyển thành exception Python, không làm sập tiến trình.

## Kỷ luật "Python tham chiếu trước, Rust sau"
1. Interface định nghĩa ở Python (`Protocol`) — xem `docs/specs/02-retrieval.md`.
2. Bản Python tham chiếu chạy được end-to-end (M1).
3. Bản Rust implement cùng interface (M3); **golden test** bắt buộc cho kết quả tương đương.
4. `bench/` đo Python vs Rust; chỉ giữ Rust nếu cải thiện đo được. Không có số đo → không tuyên bố nhanh hơn.

## Module & phạm vi

| Module | Crate gợi ý | Việc làm | Giai đoạn |
|---|---|---|---|
| `lexical` | `tantivy` | Index/search BM25, filter theo metadata (`doc_type`, `module`, `is_active`), tokenizer tuỳ biến (syllable/bigram, NFC, bỏ dấu tuỳ chọn) | M3 (ưu tiên 1) |
| `parse_xlsx` / `parse_csv` | `calamine`, `csv` | Đọc sheet → `Block(kind=row)` với `fields`, `loc` (sheet,row) | M3 |
| `parse_md` | `pulldown-cmark` | Heading tree, bảng, danh sách → `Block[]` | M3 |
| `chunk` | `tokenizers` (HF) | Structure-aware chunking theo `config/chunking.yaml` | M3 |
| `fusion` | (thuần Rust) | RRF/weighted RRF, dedupe, ghim ID-lookup | M3 |
| `metrics` | (thuần Rust) | Recall@K, MRR, nDCG, Precision@K | M3 |
| `parse_docx` | `quick-xml` + `zip` | **Hoãn.** Chỉ port nếu benchmark chứng minh cần | Sau M4 |

## Bề mặt Python (module `tm_core`)

```python
# Tất cả hàm nhận/trả cấu trúc đơn giản (dict/list/bytes/str) hoặc class PyO3 nhỏ.
tm_core.parse_xlsx(data: bytes, mapping: dict | None) -> dict   # ParsedDocument JSON
tm_core.parse_md(text: str) -> dict
tm_core.chunk(parsed: dict, cfg: dict) -> list[dict]            # ChunkDoc[]

class LexicalIndex:
    def __init__(self, path: str, cfg: dict) -> None: ...
    def upsert(self, chunks: list[dict]) -> None
    def delete(self, chunk_ids: list[str]) -> None
    def search(self, q: str, k: int, filters: dict) -> list[dict]  # {chunk_id, score}
    def rebuild(self, chunks: Iterable[dict]) -> None             # dựng lại từ Postgres
    def stats(self) -> dict

tm_core.rrf(rankings: list[list[str]], k: int, weights: list[float] | None) -> list[tuple[str, float]]
tm_core.metrics(retrieved: list[list[str]], gold: list[list[str]], ks: list[int]) -> dict
```

Quy ước lỗi: mọi lỗi Rust → `tm_core.TmCoreError` (có `code` + message), **không panic** qua biên FFI.
Giải phóng GIL cho các tác vụ nặng (`py.allow_threads`).

## Schema trao đổi (JSON, ổn định)

```
ParsedDocument { doc_type, language_hint, blocks: Block[], warnings: string[] }
Block { kind, text, level?, section_path: string[], loc: Loc, table?, fields? }
Loc { page?, sheet?, row?, col_range?, paragraph_idx? }
ChunkDoc { id, ordinal, text, text_for_embedding, section_path, loc, requirement_ids,
           doc_type, module, is_active, token_count }
```

Thay đổi schema = cập nhật spec này + golden test + bản Python tham chiếu trong cùng commit.

## Index tantivy là dữ liệu dẫn xuất
- Thư mục index nằm trong volume; **nguồn thật là bảng `chunks`**.
- `make reindex` gọi `LexicalIndex.rebuild` từ Postgres; chạy được sau khi đổi tokenizer/schema.
- Xoá/vô hiệu hoá chunk ở Postgres phải đi kèm `delete` ở index (cùng service, có test nhất quán).
- Ghi (commit) index theo batch; truy vấn chạy trên reader đã reload có kiểm soát.

## Kiểm thử
- Rust: unit test từng module, property test cho RRF/metrics, fixture Excel/MD thực tế (merged cell, ô trống, Unicode tiếng Việt).
- Python: pytest kiểm tra binding, kiểu dữ liệu, lỗi chuyển thành `TmCoreError`.
- **Golden/equivalence test**: Python tham chiếu vs Rust cho cùng input → cùng `ParsedDocument`/chunk; lexical top-K tương đương
  (cho phép sai khác thứ hạng nhỏ do tokenizer, phải ghi rõ ngưỡng chấp nhận).
- Metric Rust phải khớp bản Python đối chiếu trên bộ ví dụ cố định.

## Benchmark (`bench/`)

| Phép đo | Cách đo |
|---|---|
| Parse xlsx | Thời gian + RAM đỉnh cho file 1k/10k/50k dòng: `openpyxl` vs `calamine` |
| Index lexical | Thời gian index N chunk: Python reference vs tantivy |
| Search lexical | p50/p95 cho tập truy vấn cố định, khi corpus 10k/100k chunk |
| Chunking | Thời gian trên cùng tập tài liệu |
| End-to-end | Thời gian truy vấn **toàn pipeline** để cho thấy tỷ trọng phần Rust so với embedding/LLM |

Kết quả lưu ở `bench/results/` kèm môi trường (CPU, RAM, phiên bản). Không điền số ước tính.

## Build & CI
- `maturin develop` (dev), `maturin build --release` (image). `cargo fmt`, `cargo clippy -D warnings`, `cargo test`.
- CI cache `~/.cargo` và `target/`. Image `api` build wheel nhiều tầng (builder Rust → runtime Python slim).
- Không `unsafe` nếu chưa có ADR. Không `unwrap/expect` ngoài test.

## Acceptance
- Với mỗi module Rust đã port: golden test xanh + có dòng benchmark thật so với Python.
- Module nào không cải thiện đo được → ghi vào `docs/adr/` và giữ bản Python.
