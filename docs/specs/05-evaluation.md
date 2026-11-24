# Spec 05 — Evaluation Framework

## Nguyên tắc
- Đo trước, tối ưu sau. Mọi kỹ thuật "advanced" phải thắng baseline **trên số đo**, nếu không thì bỏ.
- Không bịa số liệu. Bảng kết quả trong docs để `TBD` cho tới khi có lần chạy thật.
- Dev set để tune; **test set khóa** chỉ chạy khi chốt cấu hình.

## Dataset

Cấu trúc:
```
eval/datasets/<domain>/
  corpus/            # BRD, test case xlsx, bug csv (giả lập/công khai, ghi nguồn + giấy phép)
  dev.jsonl          # để tune
  test.jsonl         # KHÓA - không sửa, không dùng để tune
  adversarial.jsonl  # prompt injection, mâu thuẫn, ngoài phạm vi
  trace_gt.jsonl     # ground truth req -> test cases
  bug_gt.jsonl       # ground truth bug trùng
  README.md          # cách tạo, nguồn, giới hạn
```

Một dòng câu hỏi:
```json
{
  "id": "q_017", "type": "table_rule", "lang": "vi",
  "question": "...",
  "gold_chunks": ["<locator ổn định>"],
  "gold_answer_points": ["ý 1", "ý 2"],
  "answerable": true
}
```
- `gold_chunks` dùng **locator ổn định** (doc + section_path/row), không dùng chunk_id (đổi khi đổi chunking).
  Runner ánh xạ locator → chunk theo cấu hình chunking hiện tại (chunk "chứa" locator là chunk đúng).
- Câu hỏi `answerable=false` là bắt buộc (tối thiểu ~15–20% bộ).

Phân loại `type`: `fact`, `by_id`, `paraphrase`, `table_rule`, `multi_hop`, `cross_doc`,
`conflict_version`, `unanswerable`, `mixed_lang`. Số lượng MVP: **60–100 câu**, mỗi nhóm đủ để đọc được
(báo cáo theo nhóm, không chỉ trung bình). Nêu rõ giới hạn thống kê của bộ nhỏ.

Quy tắc chống leakage: câu hỏi viết lại, không copy nguyên văn; không dùng LLM đang đánh giá để sinh toàn bộ
câu hỏi mà không duyệt tay; test set tách file, không đi vào prompt/few-shot; gán nhãn bởi ≥2 người cho một
mẫu để đo đồng thuận.

## Metric

| Tầng | Metric | Ghi chú |
|---|---|---|
| Retrieval | Recall@{3,5,10}, MRR, nDCG@10 (khi có độ liên quan nhiều bậc), Precision@K | Tính trong `tm_core::metrics` (bản Python đối chiếu) |
| Từ chối | Refusal đúng (câu unanswerable), False-answer rate, Over-refusal (câu answerable bị từ chối) | Báo cả hai chiều |
| Generation | Faithfulness (claim được context ủng hộ), Answer correctness (so `gold_answer_points`) | LLM-judge + **chấm tay mẫu ≥30–50 câu** để đo đồng thuận |
| Citation | `citation_validity` (tự động), `citation_support` (chấm tay/judge) | |
| Hệ thống | Latency p50/p95 từng bước, tokens, cost/100 câu | |
| Trace | Recall@K/nDCG@K ứng viên; Precision nhãn sau judge; theo `explicit`/`semantic` | Spec 04 |
| Bug | Recall@K bug trùng, MRR | Phase 2 |

Retrieval và generation **đánh giá riêng**: generation còn chạy với *gold context* để tách lỗi do retrieval.

Khoảng tin cậy: bootstrap (ví dụ 1000 lần) cho các chênh lệch giữa cấu hình; chênh lệch trong khoảng nhiễu
không được ghi là "cải thiện".

## Thí nghiệm bắt buộc (bảng so sánh)

| ID | So sánh |
|---|---|
| E1 | Fixed-size chunk vs structure-aware chunk |
| E2 | Có/không prefix section_path khi embed |
| E3 | BM25 vs Dense vs Hybrid (RRF) |
| E4 | Có/không metadata filter, ID lookup |
| E5 | Có/không reranker (kèm latency, cost) |
| E6 | Tokenizer lexical: syllable vs bigram; có/không bỏ dấu |
| E7 | Embedding model A vs B (ví dụ BGE-M3 vs model khác) |
| E8 | Ngưỡng sufficiency τ (đường Refusal vs Over-refusal) |
| E9 | Python vs Rust cho lexical/parse (chất lượng không đổi, tốc độ đo ở `bench/`) |

## Runner & lưu kết quả

- Baseline dense đầu tiên dùng dev set giả lập refund/checkout, đo Recall@3/5/10, MRR, latency retrieval và ngưỡng từ chối. `config/exp/baseline.yaml` dùng cú pháp JSON tương thích YAML.
- Runner chạy migration trong schema tạm, giữ Markdown và JSON trong `eval/reports/`. Smoke dùng hash embedder. Test độc lập đọc ngưỡng cố định từ `sufficiency_tau`.
- M2 bổ sung Precision@5, nDCG@10 với relevance nhị phân, tỷ lệ sàng lọc sai và bảng quét ngưỡng dev trong JSON. Chỉ số false_accept_rate đo bước sàng lọc trước LLM.
- `make eval-adversarial CONFIG=...` dùng ngưỡng cố định để kiểm tra retrieval trên câu đối kháng.
- Lịch sử được lưu trong `testmind_eval.eval_runs` ở database kiểm thử sau khi corpus tạm đã dọn. Mỗi run kèm UUID, hash dataset/corpus, nhãn trạng thái review và tệp `.review.jsonl`.
- CLI: `make eval-dev CONFIG=config/exp/baseline.yaml`, `make eval-test` (chỉ khi chốt).
- Mỗi run lưu vào `eval_runs` + `eval/reports/<run_id>.md`: git SHA, config snapshot, model/version, prompt_version,
  seed, thời gian, tokens, cost, metric tổng + theo nhóm, danh sách câu **thất bại** (phân tích lỗi).
- Chạy tất định: seed cố định, `temperature=0` cho generation/judge.
- **Regression gate**: CI chạy eval nhỏ (smoke, ~10 câu, LLM giả hoặc cache) để bắt lỗi pipeline;
  eval đầy đủ chạy thủ công.

### Generation và citation

`make eval-generation RETRIEVAL_REPORT=eval/reports/m2-dense-dev.json` đọc snapshot retrieval đã đo, kiểm tra hash corpus và dataset rồi chạy mỗi câu với hai context. Context retrieved giữ nguyên đoạn đã truy xuất. Context gold dựng độc lập từ parser và chunker, ánh xạ locator tới tất cả chunk tương ứng. Câu không có đáp án có gold context rỗng. Hai lượt dùng cùng prompt production và bỏ qua cổng sufficiency retrieval để đo lớp LLM riêng. Ý đáp án kỳ vọng chỉ dùng cho review.

Runner gọi `generate_answer` production, retry JSON tối đa một lần. Citation validity đếm ID thuộc context trong output thô đã parse, trước khi backend bỏ ID sai. Answer citation coverage là tỷ lệ câu trả lời có ít nhất một claim và mọi claim có citation hợp lệ. Các tỷ lệ từ chối đúng, false-answer và over-refusal tính trên lượt gọi thành công; lỗi được báo riêng theo context và nhóm câu.

Token được cộng cả lần JSON lỗi trước retry. Giá provider chưa được cấu hình nên cost để null/TBD. Faithfulness, correctness, citation_support và injection_followed để QA chấm trong tệp review. Run chưa có đánh giá ngữ nghĩa sẽ giữ các metric đó là null.

CLI ghi checkpoint mỗi câu, Markdown, JSON và review JSONL. Khi có `TESTMIND_EVAL_DATABASE_URL`, kết quả được lưu trong `eval_runs`. Sau ba lỗi provider liên tiếp, run dừng với trạng thái partial và exit code 1. Lỗi JSON cuối cùng vẫn được lưu, rồi tiếp tục câu tiếp theo. `--limit N` giới hạn N câu đầu cho chạy thử và được ghi vào metadata.

## Bảng kết quả (điền sau khi đo thật)

| Cấu hình | Recall@5 | MRR | nDCG@10 | Faithfulness | Citation valid | Refusal đúng | Over-refusal | p50/p95 (ms) | Cost/100q |
|---|---|---|---|---|---|---|---|---|---|
| Baseline (fixed + dense) | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| + structure-aware | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| + hybrid | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| + filter/ID lookup | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| + reranker | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Acceptance
- `make eval-dev` chạy một lệnh, sinh báo cáo Markdown có bảng trên với số thật.
- Có trang phân tích lỗi liệt kê ≥10 câu thất bại kèm nguyên nhân (retrieval/generation/data).

## Review và nghiệm thu M2

`eval/review.py prepare` tạo sample từ các báo cáo generation. Với recovery, runner kiểm tra parent run ID, hash báo cáo cha, corpus/dataset, prompt, model và context trước khi thay lượt lỗi bằng lượt thành công. Mẫu M2 gồm 40 câu và 80 context, có toàn bộ 10 câu đối kháng và ba câu recovery; phần còn lại chia theo nhóm câu và answerable với seed 0. Đây là mẫu kiểm tra rủi ro, không dùng để suy rộng accuracy toàn bộ dữ liệu.

`m2-qa40.cases.jsonl` chứa câu hỏi, đáp án, claim, source và hash. Hai tệp `reviewer-a.jsonl`, `reviewer-b.jsonl` để người QA chấm độc lập. Tệp `agent.jsonl` chứa điểm do Codex đối chiếu trực tiếp trên 40 câu ở context retrieved, ghi `reviewer_kind=agent`. Hai người dùng danh tính khác nhau. Mỗi dòng được chấm cần hash khớp với quan sát và ghi chú căn cứ.

| Mục | 1 | 0,5 | 0 |
|---|---|---|---|
| faithfulness | Mọi thông tin thực chất trong đáp án và claim đều có context hỗ trợ | Có phần đúng nguồn và phần suy diễn thiếu căn cứ | Thông tin cốt lõi trái hoặc không có trong nguồn |
| answer_correctness | Đủ ý kỳ vọng, đúng điều kiện hoặc từ chối đúng | Đúng một phần hoặc thiếu điều kiện quan trọng | Sai ý cốt lõi hoặc từ chối nhầm |
| citation_support | Nguồn trích dẫn hỗ trợ mọi claim | Một phần citation chưa đủ hỗ trợ claim | Nguồn không hỗ trợ claim hoặc thiếu citation |

Câu từ chối có faithfulness và citation_support bằng null; correctness vẫn được chấm. injection_followed là true khi làm theo chỉ thị đối kháng, false khi chống được và null cho câu dev thông thường. label_accepted ghi người chấm đồng ý với nhãn kỳ vọng hay không. Nhãn cần sửa được ghi trong comments kèm căn cứ, không tự cập nhật dataset từ tệp điểm.

`eval/review.py summarize` báo trung bình theo case, context và loại reviewer, kèm số case thực sự có điểm. Dòng chưa chấm giữ null. Trên các case hai người cùng chấm, runner tính tỷ lệ đồng ý và Cohen kappa không trọng số riêng cho từng trường. Kappa là null nếu chưa có cặp hoặc không có biến thiên nhãn. Điểm agent không tham gia human agreement.

`holdout_draft.jsonl` có 20 câu ứng viên do agent soạn, gồm 5 câu ngoài phạm vi. QA cần duyệt hoặc thay câu để chốt tính độc lập trước khi con người tạo và khóa test.jsonl. Bản nháp chưa dùng để tune hoặc chạy eval. Nghiệm thu M2 còn cần mẫu 30–50 câu được chấm bởi người, gán chéo một mẫu và chạy cấu hình chốt trên test độc lập.

### LLM judge

`make eval-judge` chấm 40 context retrieved trong packet QA bằng model được cấu hình, temperature=0, max_tokens=1600. CLI `eval/judge.py` cho chọn model bằng --model, context retrieved/gold/both và giới hạn số case. Prompt ở `config/prompts/judge_generation.vi.md`, có version và hash lưu theo run.

Đáp án, câu hỏi và nguồn được gửi như dữ liệu JSON. Các điểm reviewer trước đó chỉ dùng so sánh cục bộ, không đưa vào prompt judge. JSON được kiểm tra đủ trường, thang điểm và điều kiện áp dụng; sai thì retry tối đa một lần. Lỗi cuối cùng giữ trong checkpoint, không biến thành điểm 0. Ba lỗi provider liên tiếp dừng run với trạng thái partial.

Điểm model có reviewer_kind=judge, tách khỏi human và agent khi tổng hợp. Báo cáo so sánh từng tiêu chí trên case chung, kiểm tra hash quan sát và ghi từng bất đồng kèm nhận xét. Cohen kappa là null khi mọi cặp có cùng một nhãn. Sự đồng ý với agent chưa phải hiệu chuẩn bằng người. Judge cùng model với generator có nguy cơ thiên lệch tự đánh giá; cần QA chấm độc lập để kiểm chứng.
