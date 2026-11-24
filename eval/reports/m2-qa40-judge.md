# Đối chiếu LLM judge

Model deepseek-ai/DeepSeek-V4.1-Flash-1017. Prompt judge.generation.vi.1.
Đã thử 40 case; có 40 điểm hợp lệ.
Đây là điểm model, cần đối chiếu với người QA trước khi dùng để nghiệm thu.
Nếu judge và generator dùng cùng model, kết quả có nguy cơ thiên lệch tự đánh giá.

| Reviewer đối chiếu | Loại | Tiêu chí | Số cặp | Đồng ý | Cohen kappa |
|---|---|---|---:|---:|---:|
| Codex | agent | faithfulness | 32 | 1.000 | TBD |
| Codex | agent | answer_correctness | 40 | 1.000 | TBD |
| Codex | agent | citation_support | 32 | 1.000 | TBD |
| Codex | agent | injection_followed | 10 | 1.000 | TBD |
| Codex | agent | label_accepted | 40 | 1.000 | TBD |

## Trường hợp bất đồng

| Case | Tiêu chí | Điểm trước | Judge | Nhận xét judge |
|---|---|---:|---:|---|

## Thông tin lần chạy

```json
{
  "run_id": "fba059b6-eae1-43be-9e07-8c62c819df82",
  "reviewer": "judge:deepseek-ai/DeepSeek-V4.1-Flash-1017:judge.generation.vi.1:fba059b6-eae1-43be-9e07-8c62c819df82",
  "model": "deepseek-ai/DeepSeek-V4.1-Flash-1017",
  "prompt_version": "judge.generation.vi.1",
  "prompt_sha256": "da4e3e999a3edaad401f077225d8232b33aecdfa561b4d3341750181977b5073",
  "cases_sha256": "1d2fd3d808e329d73093d23ab5b219ff1ec2be9bded08256d7756183760fd697",
  "comparison_sha256": {
    "eval/reports/m2-qa40.agent.jsonl": "08d9909eb2642d7eb267206d1f37d25914716a49e80c62f8150ff81d8fab01a3"
  },
  "context": "retrieved",
  "max_tokens": 1600,
  "temperature": 0,
  "planned_cases": 40,
  "attempted_cases": 40,
  "complete": true,
  "tokens_in": 139675,
  "tokens_out": 18698,
  "cost": null,
  "started_utc": "2026-11-24T12:17:26.881747+00:00",
  "elapsed_seconds": 73.51484,
  "git_sha": "4838f5b80838cbfada5f86eaae64e845e7347340",
  "working_tree_dirty": true
}
```
