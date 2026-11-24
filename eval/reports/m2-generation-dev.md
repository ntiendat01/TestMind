# Đánh giá generation và citation

Model deepseek-ai/DeepSeek-V4.1-Flash-1017. Run 4ab80b2f-a197-4ae4-8593-f8e54e1a5741.
Số lượt dự kiến 120, đã thử 120, hoàn tất False.
Mỗi câu chạy hai lần với prompt chung, một lần dùng context truy xuất đã lưu và một lần dùng nguồn gold. Cả hai lượt bỏ qua cổng ngưỡng retrieval để đo riêng LLM.
Với câu không có đáp án, gold context rỗng. Ý đáp án kỳ vọng chỉ xuất trong tệp review.
Citation validity kiểm tra membership trên citation thô trước bộ lọc backend. Citation support, faithfulness, correctness và việc làm theo injection chờ QA chấm.
Lỗi API hoặc JSON được đếm riêng và loại khỏi mẫu số tỷ lệ đáp án. Chi phí để TBD khi chưa có giá provider được xác minh.

| Context | Mẫu | Lỗi | Từ chối đúng | Trả lời ngoài phạm vi | Từ chối nhầm | Citation validity | Answer citation coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| retrieved | 60 | 3 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| gold | 60 | 0 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 |

retrieved token vào 138737, token ra 27514. Chi phí TBD.
retrieved latency p50 1514.7 ms, p95 2268.6 ms.
gold token vào 22532, token ra 17028. Chi phí TBD.
gold latency p50 1130.2 ms, p95 2030.9 ms.

## Câu cần xem lại

| ID | Context | Vấn đề tự động phát hiện |
|---|---|---|
| q34 | retrieved | llm_response_invalid |
| q38 | retrieved | llm_response_invalid |
| q48 | retrieved | llm_response_invalid |

## Thông tin lần chạy

```json
{
  "run_id": "4ab80b2f-a197-4ae4-8593-f8e54e1a5741",
  "dataset": "refund-checkout",
  "split": "dev",
  "mode": "generation",
  "model": "deepseek-ai/DeepSeek-V4.1-Flash-1017",
  "prompt_version": "answer.vi.1",
  "prompt_sha256": "afe97c14fe9877ce747159cdef7a5f94d5f70151553c1a04d4faa421a6bbbfa3",
  "retrieval_report_sha256": "c26c886fbd83032ff62856a6fb9b904706570e2c438dd9783b8e20f08775acea",
  "retrieval_run_id": "90d83071-f1ca-4e58-936d-52d31251d208",
  "dataset_sha256": "defeaa6e6a2d63945c5f238e57d0ca0aa1eaf82896b9569ab0d65e43362e5686",
  "corpus_sha256": "74024d7b7e100ff44dd490dbc26fa0300d380f0eea0fc696d5e77d0498232957",
  "labels_status": "agent_draft_pending_human_review",
  "git_sha": "77fdc9a8a2354a31039c8d9dc842351a24ad3826",
  "working_tree_dirty": true,
  "started_utc": "2026-11-24T11:49:36.741845+00:00",
  "elapsed_seconds": 180.038627,
  "config": {
    "temperature": 0,
    "max_tokens": 800,
    "limit": null
  },
  "planned_samples": 120,
  "attempted_samples": 120,
  "complete": false
}
```
