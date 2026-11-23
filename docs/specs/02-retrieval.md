# Spec 02 — Retrieval Pipeline

## Mục tiêu
Lấy đúng bằng chứng (high Recall@K) với latency chấp nhận được; mọi bước bật/tắt bằng config để eval A/B.

## Pipeline

```
query
 → analyze        (phát hiện ID, filter ngầm, ngôn ngữ)
 → [ID lookup | dense | lexical]   (song song)
 → fusion (RRF)
 → (rerank)       (tuỳ chọn, mặc định TẮT cho tới khi eval chứng minh)
 → context build  (dedupe, thêm heading cha, giới hạn token)
 → sufficiency check
```

## 1. Query analysis (không dùng LLM trong MVP)

- Regex ID: `REQ-\d+`, `TC-\d+`, `BUG-\d+` (cấu hình được) → **exact lookup** ưu tiên cao nhất.
- Filter rõ ràng từ request: `doc_types[]`, `module`, `version` (mặc định chỉ `is_active`).
- Query rewriting/decomposition: **không có trong MVP**. Chỉ thêm khi eval cho thấy nhóm câu multi-hop
  thất bại nhiều (xem `docs/specs/05-evaluation.md`).

## 2. Các nhánh truy xuất

| Nhánh | Cách làm | Top-N mặc định |
|---|---|---|
| ID lookup | SQL trên `requirement_ids`/`*_key` | không giới hạn (thường ít) |
| Dense | embed query → pgvector cosine, áp filter metadata | 30 |
| Lexical | tantivy BM25 (Python reference: `rank-bm25`/Postgres FTS) | 30 |

Filter áp dụng **ở cả hai nhánh** (không lọc sau, tránh mất kết quả).

## 3. Fusion

**RRF**: `score(d) = Σ 1 / (k + rank_i(d))`, `k=60` (cấu hình). Có tuỳ chọn weighted RRF để thử nghiệm.
Kết quả ID lookup được **ghim lên đầu**, không bị RRF hạ thứ hạng.
Dedupe theo `chunk_id`; gộp chunk liền kề cùng section nếu cấu hình bật.

## 4. Rerank (tuỳ chọn)

- Cross-encoder (`bge-reranker-v2-m3`) trên top-20 sau fusion → giữ top-8.
- Mặc định `enabled=false`. Bật khi và chỉ khi eval báo Δ nDCG/MRR dương **vượt nhiễu** (bootstrap CI)
  và latency chấp nhận được.

## 5. Context build

- Giữ thứ tự theo điểm; thêm `section_path` vào đầu mỗi đoạn dẫn.
- Giới hạn `context_token_budget` (mặc định 3000, cấu hình).
- Mỗi đoạn mang `chunk_id` để LLM trích dẫn (xem spec 03).

## 6. Sufficiency check (từ chối ngoài phạm vi)

- Điều kiện thiếu bằng chứng (ví dụ): không có ID khớp **và** top-1 `rerank/dense score` dưới ngưỡng `τ`.
- `τ` **không đặt cảm tính**: hiệu chỉnh trên dev set (câu có đáp án vs không có đáp án) và lưu trong config.
- Luồng dense đọc ngưỡng tùy chọn từ `RETRIEVAL_MIN_SIMILARITY` (cosine similarity). Khi chưa đặt, API từ chối trước LLM nếu không lấy được chunk nào. Báo cáo dev lưu ngưỡng ứng viên để xác nhận trên test độc lập trước khi áp dụng mặc định.
- Khi thiếu: trả `insufficient_evidence=true` kèm các nguồn gần nhất (để người dùng tự xem), không gọi LLM sinh câu trả lời.
- LLM cũng có quyền trả `insufficient_evidence` (lớp bảo vệ thứ hai).

## Interface (Python)

```python
class Retriever(Protocol):
    async def retrieve(self, req: RetrievalRequest) -> RetrievalResult: ...

class LexicalIndex(Protocol):          # Python reference & tm_core đều implement
    def upsert(self, chunks: list[ChunkDoc]) -> None: ...
    def delete(self, chunk_ids: list[str]) -> None: ...
    def search(self, q: str, k: int, filters: Filters) -> list[Hit]: ...
```

`RetrievalResult` gồm: `hits[]` (chunk_id, score từng nhánh, rank), `timings` theo bước, `config_snapshot`.

## Tiếng Việt

- Lexical: tokenizer thử 2 chế độ (syllable/whitespace, và bigram âm tiết); chọn theo eval, không theo cảm tính.
- Chuẩn hoá Unicode NFC, tuỳ chọn bỏ dấu cho nhánh lexical (A/B).
- Câu hỏi song ngữ/trộn Anh–Việt: không dịch query trong MVP; đo riêng nhóm này.

## Test bắt buộc

- Query chứa `REQ-045` → chunk của REQ-045 ở vị trí 1.
- Filter `module` loại đúng chunk ngoài module (cả hai nhánh).
- Chunk `is_active=false` không bao giờ xuất hiện.
- Hai cấu hình (dense-only vs hybrid) chạy trên cùng input cho kết quả tất định (seed cố định).
- Bản Rust `LexicalIndex` cho top-K **giống hoặc tương đương** bản Python tham chiếu trên fixture.

## Acceptance
- `make eval-dev` in bảng Recall@K/MRR cho: BM25 / Dense / Hybrid / Hybrid+Rerank, tách theo nhóm câu hỏi.
- Latency từng bước nằm trong `RetrievalResult.timings`.
