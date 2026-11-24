# Đánh giá generation và citation

Model deepseek-ai/DeepSeek-V4.1-Flash-1017. Run 171f08a7-0568-4033-86ba-1e97d250331c.
Số lượt dự kiến 3, đã thử 3, hoàn tất True.
Lượt recovery chạy lại riêng ba context retrieved lỗi JSON của q34, q38 và q48, với max_tokens=1600. Báo cáo baseline dev ở max_tokens=800 được giữ nguyên để đối chiếu.
Với câu không có đáp án, gold context rỗng. Ý đáp án kỳ vọng chỉ xuất trong tệp review.
Citation validity kiểm tra membership trên citation thô trước bộ lọc backend. Citation support, faithfulness, correctness và việc làm theo injection chờ QA chấm.
Lỗi API hoặc JSON được đếm riêng và loại khỏi mẫu số tỷ lệ đáp án. Chi phí để TBD khi chưa có giá provider được xác minh.

| Context | Mẫu | Lỗi | Từ chối đúng | Trả lời ngoài phạm vi | Từ chối nhầm | Citation validity | Answer citation coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| retrieved | 3 | 0 | TBD | TBD | 0.000 | 1.000 | 1.000 |
| gold | 0 | 0 | TBD | TBD | TBD | TBD | TBD |

retrieved token vào 6507, token ra 3416. Chi phí TBD.
retrieved latency p50 3329.8 ms, p95 3348.5 ms.
gold token vào 0, token ra 0. Chi phí TBD.

## Câu cần xem lại

| ID | Context | Vấn đề tự động phát hiện |
|---|---|---|

## Thông tin lần chạy

```json
{
  "run_id": "171f08a7-0568-4033-86ba-1e97d250331c",
  "dataset": "refund-checkout",
  "split": "dev",
  "mode": "generation_recovery",
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
  "started_utc": "2026-11-24T11:52:47.817854+00:00",
  "elapsed_seconds": 10.060135,
  "config": {
    "temperature": 0,
    "max_tokens": 1600,
    "retry_only": [
      [
        "q34",
        "retrieved"
      ],
      [
        "q38",
        "retrieved"
      ],
      [
        "q48",
        "retrieved"
      ]
    ]
  },
  "planned_samples": 3,
  "attempted_samples": 3,
  "complete": true,
  "parent_run_id": "4ab80b2f-a197-4ae4-8593-f8e54e1a5741",
  "parent_report_sha256": "247ac7f3756eef24d291434123762fa253c996e5bac32681c1fc13101e70fa21",
  "finish_reasons": [
    "stop",
    "stop",
    "stop"
  ]
}
```
