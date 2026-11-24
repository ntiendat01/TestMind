# Corpus mẫu hoàn tiền và checkout

Tất cả tài liệu và câu hỏi được viết riêng cho TestMind. Mã requirement, test case và điều kiện nghiệp vụ đều giả lập. Dữ liệu dùng cho demo và kiểm thử trong repo. Corpus chưa có giấy phép phát hành riêng và không dùng dữ liệu của bên thứ ba.

- `corpus/` gồm quy định hoàn tiền, checkout và bộ test case CSV.
- `dev.jsonl` dùng để thử truy xuất và hiệu chỉnh điểm từ chối. Nhãn nguồn được viết theo section hoặc số dòng gốc.
- `test.jsonl` sẽ do người phụ trách dữ liệu tạo và khóa sau khi rà soát nhãn. Điểm trên dev set có thể cao do corpus nhỏ và câu hỏi được viết từ cùng bộ quy tắc.

## Phiên bản M2

- Dev có 60 câu, gồm 15 câu ngoài phạm vi, câu tra ID, bảng, diễn đạt lại, nhiều nguồn và Anh–Việt.
- `adversarial.jsonl` có 10 câu thử giả mạo chỉ thị, ép suy đoán và đòi thông tin bí mật. `corpus/adversarial.md` chứa chuỗi injection giả lập để đưa vào context.
- Các câu và nhãn mở rộng do agent soạn từ corpus, **chưa được con người duyệt hoặc gán nhãn chéo**. Đây là dữ liệu nháp phục vụ phát triển. Chưa có nhóm conflict_version vì corpus chưa chứa lịch sử phiên bản đối nghịch.
- Mỗi lần chạy xuất `.review.jsonl` để QA điền `reviewer`, `label_accepted` và `comments`. Cần ít nhất hai người kiểm tra một mẫu trước khi chốt ground truth.
- Chưa có test set khóa. Người phụ trách QA cần viết bộ holdout độc lập sau khi rà soát corpus. Runner yêu cầu ngưỡng cố định khi chạy test hoặc adversarial.
- Nguồn do dự án tự tạo. Việc phát hành lại corpus cần chủ dự án chốt giấy phép.

## Review và holdout

`eval/reports/m2-qa40.cases.jsonl` giữ 80 context cho 40 câu được chọn bằng seed 0, gồm 30 câu dev và 10 câu đối kháng. Hai biểu mẫu reviewer-a/reviewer-b có điểm trống để người QA chấm độc lập. Điểm trong agent.jsonl do Codex ghi cho 40 context retrieved, chưa thay thế lượt gán nhãn chéo bởi người.

`holdout_draft.jsonl` có 20 ứng viên mới, gồm 15 câu có đáp án và 5 câu ngoài phạm vi. Chúng do agent soạn từ cùng corpus và chờ QA kiểm tra tính độc lập. Bản nháp chưa được chạy eval hoặc dùng tune. Người phụ trách dữ liệu tạo và khóa test.jsonl sau khi chốt câu hỏi và nhãn.
