# ADR 0005 — Parser DOCX bằng python-docx

## Trạng thái

Chấp nhận.

## Quyết định

Dùng `python-docx` 1.2 trở lên để đọc đoạn và bảng theo thứ tự trong phần nội dung chính của Word. Vị trí nguồn dùng chỉ số khối và số dòng trong bảng, vì số trang phụ thuộc vào ứng dụng dàn trang.

Đọc ZIP/XML thủ công sẽ phải tự xử lý thứ tự block, kiểu heading và ô gộp. M1 dùng Python làm bản tham chiếu, phù hợp với quyết định hoãn parser Rust cho DOCX.
