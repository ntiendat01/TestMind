# Baseline dense trên dev set

Bộ refund-checkout có 60 câu, gồm 45 câu có đáp án.
Embedding dùng **BAAI/bge-m3** và search cosine trên pgvector.
Lần chạy đo retrieval và sàng lọc theo điểm. Chi phí API LLM bằng 0 vì bước này dừng ở retrieval.

| Nhóm | Số câu | Recall@3 | Recall@5 | Recall@10 | MRR | Precision@5 | nDCG@10 binary |
|---|---:|---:|---:|---:|---:|---:|---:|
| Tất cả | 60 | 0.956 | 0.989 | 1.000 | 0.931 | 0.231 | 0.938 |
| by_id | 7 | 1.000 | 1.000 | 1.000 | 1.000 | 0.200 | 1.000 |
| cross_doc | 5 | 0.900 | 1.000 | 1.000 | 1.000 | 0.400 | 0.959 |
| fact | 9 | 1.000 | 1.000 | 1.000 | 0.926 | 0.200 | 0.944 |
| mixed_lang | 6 | 1.000 | 1.000 | 1.000 | 0.917 | 0.200 | 0.938 |
| multi_hop | 5 | 0.900 | 0.900 | 1.000 | 1.000 | 0.280 | 0.947 |
| paraphrase | 6 | 0.833 | 1.000 | 1.000 | 0.792 | 0.200 | 0.844 |
| table_rule | 7 | 1.000 | 1.000 | 1.000 | 0.905 | 0.200 | 0.929 |
| unanswerable | 15 | — | — | — | — | — | — |

Latency retrieval p50 435.8 ms và p95 734.4 ms sau khi index xong.

## Sàng lọc câu ngoài phạm vi

Ngưỡng ứng viên trên dev set là `0.52849605509662401`.
Có 11/15 câu ngoài phạm vi vượt ngưỡng và 1/45 câu có đáp án nằm dưới ngưỡng.
Các tỷ lệ đo quyết định sàng lọc theo điểm trước LLM. Chất lượng câu trả lời và citation_support chờ lượt đánh giá generation.
Chọn ngưỡng giảm tổng hai loại lỗi. Khi hòa, ưu tiên giảm số câu ngoài phạm vi vượt ngưỡng.
Mẫu dev nhỏ dùng để tìm lỗi và thử ngưỡng. Cần kiểm tra trên bộ test độc lập trước khi bật mặc định.

## Câu cần xem lại

| ID | Câu hỏi | Vấn đề | Nguồn đầu tiên | Nguồn kỳ vọng |
|---|---|---|---|---|
| q16 | Phí hoàn tiền quốc tế là bao nhiêu phần trăm với thẻ phát hành ở nước ngoài? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | testcases.csv#row:3 | — |
| q19 | Sau khi đổi địa chỉ, phí giao hàng cụ thể đến Đà Nẵng là bao nhiêu? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | checkout.md#Checkout > Phí vận chuyển | — |
| q22 | Tôi trả bằng ví và thẻ. Shop có thể gom toàn bộ tiền hoàn vào ví không? | Retrieval: thiếu nguồn chuẩn trong top 3 | testcases.csv#row:3 | refund.md#Hoàn tiền > Phương thức hoàn |
| q36 | REQ-102 và TC-102 cùng bảo vệ hệ thống khỏi kết quả sai nào? | Sàng lọc: có đáp án nhưng dưới ngưỡng, Retrieval: thiếu nguồn chuẩn trong top 3 | testcases.csv#row:6 | checkout.md#Checkout > Giao dịch trùng, testcases.csv#row:6 |
| q49 | Một đơn chưa bàn giao muốn hoàn toàn phần cần đáp ứng mốc thời gian nào và hoàn về phương thức nào? | Retrieval: thiếu nguồn chuẩn trong top 3 | refund.md#Hoàn tiền > Hạn gửi yêu cầu | refund.md#Hoàn tiền > Hạn gửi yêu cầu, refund.md#Hoàn tiền > Phương thức hoàn |
| q51 | REQ-102 quy định thời gian lưu khóa idempotency là bao nhiêu giờ? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | testcases.csv#row:6 | — |
| q52 | Trong vòng 48 giờ báo hàng hỏng, shop có chịu phí gửi trả không? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | refund.md#Hoàn tiền > Hàng đã giao | — |
| q53 | Sau khi provider chấp nhận hoàn, ngân hàng tối đa bao lâu mới trả tiền vào thẻ? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | checkout.md#Checkout > Thanh toán chờ xác nhận | — |
| q54 | Nếu request cùng khóa idempotency nhưng khác nội dung thì HTTP status là bao nhiêu? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | checkout.md#Checkout > Giao dịch trùng | — |
| q55 | Mã giảm giá tối thiểu phải đạt giá trị giỏ hàng bao nhiêu? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | checkout.md#Checkout > Mã giảm giá | — |
| q56 | Giữ hàng hết 15 phút nhưng webhook thành công tới muộn thì xử lý ra sao? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | checkout.md#Checkout > Thanh toán chờ xác nhận | — |
| q57 | Tên endpoint gửi yêu cầu hoàn tiền là gì? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | refund.md#Hoàn tiền > Trạng thái hoàn tiền | — |
| q58 | Một khách được hoàn tối đa bao nhiêu lần mỗi tháng? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | testcases.csv#row:3 | — |
| q59 | Nếu tiền tệ trên thẻ khác ví, tỷ giá phân bổ khoản hoàn tính thế nào? | Sàng lọc: ngoài phạm vi nhưng vượt ngưỡng | testcases.csv#row:3 | — |

## Thông tin lần chạy

```json
{
  "run_id": "90d83071-f1ca-4e58-936d-52d31251d208",
  "dataset": "refund-checkout",
  "split": "dev",
  "git_sha": "93e0069fda0cad505525b8761579e84dca933aa2",
  "working_tree_dirty": true,
  "model": "BAAI/bge-m3",
  "model_revision": "5617a9f61b028005a4858fdac845db406aefb181",
  "dataset_sha256": "defeaa6e6a2d63945c5f238e57d0ca0aa1eaf82896b9569ab0d65e43362e5686",
  "corpus_sha256": "74024d7b7e100ff44dd490dbc26fa0300d380f0eea0fc696d5e77d0498232957",
  "labels_status": "agent_draft_pending_human_review",
  "runtime": {
    "python": "3.12.16",
    "platform": "Linux-7.0.12-linuxkit-x86_64-with-glibc2.36",
    "sentence-transformers": "6.3.0",
    "torch": "2.15.0",
    "transformers": "5.24.0"
  },
  "config": {
    "dataset": "refund-checkout",
    "embedding_model": "BAAI/bge-m3",
    "retrieval_limit": 30,
    "context_token_budget": 3000,
    "sufficiency_tau": null,
    "seed": 0
  },
  "chunking": {
    "target_tokens": 400,
    "max_tokens": 800,
    "overlap_tokens": 50
  },
  "started_utc": "2026-11-24T11:21:12.198310+00:00",
  "elapsed_seconds": 86.294,
  "llm_tokens": 0,
  "llm_cost": 0
}
```
