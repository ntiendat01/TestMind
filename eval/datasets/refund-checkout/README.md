# Corpus mẫu hoàn tiền và checkout

Tất cả tài liệu và câu hỏi được viết riêng cho TestMind. Mã requirement, test case và điều kiện nghiệp vụ đều giả lập. Dữ liệu dùng cho demo và kiểm thử trong repo. Corpus chưa có giấy phép phát hành riêng và không dùng dữ liệu của bên thứ ba.

- `corpus/` gồm quy định hoàn tiền, checkout và bộ test case CSV.
- `dev.jsonl` dùng để thử truy xuất và hiệu chỉnh điểm từ chối. Nhãn nguồn được viết theo section hoặc số dòng gốc.
- `test.jsonl` sẽ do người phụ trách dữ liệu tạo và khóa sau khi rà soát nhãn. Điểm trên dev set có thể cao do corpus nhỏ và câu hỏi được viết từ cùng bộ quy tắc.
