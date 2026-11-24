# Đánh giá generation và citation

Model deepseek-ai/DeepSeek-V4.1-Flash-1017. Run 0e5c35fe-070a-4784-960c-a070a9e97d44.
Số lượt dự kiến 20, đã thử 20, hoàn tất True.
Mỗi câu chạy hai lần với prompt chung, một lần dùng context truy xuất đã lưu và một lần dùng nguồn gold. Cả hai lượt bỏ qua cổng ngưỡng retrieval để đo riêng LLM.
Với câu không có đáp án, gold context rỗng. Ý đáp án kỳ vọng chỉ xuất trong tệp review.
Citation validity kiểm tra membership trên citation thô trước bộ lọc backend. Citation support, faithfulness, correctness và việc làm theo injection chờ QA chấm.
Lỗi API hoặc JSON được đếm riêng và loại khỏi mẫu số tỷ lệ đáp án. Chi phí để TBD khi chưa có giá provider được xác minh.

| Context | Mẫu | Lỗi | Từ chối đúng | Trả lời ngoài phạm vi | Từ chối nhầm | Citation validity | Answer citation coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| retrieved | 10 | 0 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| gold | 10 | 0 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 |

retrieved token vào 21732, token ra 4306. Chi phí TBD.
retrieved latency p50 1625.1 ms, p95 2170.8 ms.
gold token vào 3375, token ra 3287. Chi phí TBD.
gold latency p50 1259.4 ms, p95 2155.1 ms.

## Câu cần xem lại

| ID | Context | Vấn đề tự động phát hiện |
|---|---|---|

## Thông tin lần chạy

```json
{
  "run_id": "0e5c35fe-070a-4784-960c-a070a9e97d44",
  "dataset": "refund-checkout",
  "split": "adversarial",
  "mode": "generation",
  "model": "deepseek-ai/DeepSeek-V4.1-Flash-1017",
  "prompt_version": "answer.vi.1",
  "prompt_sha256": "afe97c14fe9877ce747159cdef7a5f94d5f70151553c1a04d4faa421a6bbbfa3",
  "retrieval_report_sha256": "d2ae3a26b77dd19ce5435065838bdb3ba8de1ccdd1654ef8229e9ff728fb1f8b",
  "retrieval_run_id": "ebd66bd0-ab4c-4f35-9a37-d5fee37ac2e1",
  "dataset_sha256": "214beb799d93c3222ce3c6521183f1abfb6d7ee2b147db5f8515ffa3abc47d0c",
  "corpus_sha256": "74024d7b7e100ff44dd490dbc26fa0300d380f0eea0fc696d5e77d0498232957",
  "labels_status": "agent_draft_pending_human_review",
  "git_sha": "77fdc9a8a2354a31039c8d9dc842351a24ad3826",
  "working_tree_dirty": true,
  "started_utc": "2026-11-24T11:49:46.561063+00:00",
  "elapsed_seconds": 30.533022,
  "config": {
    "temperature": 0,
    "max_tokens": 800,
    "limit": null
  },
  "planned_samples": 20,
  "attempted_samples": 20,
  "complete": true
}
```
