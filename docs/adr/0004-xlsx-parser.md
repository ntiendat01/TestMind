# ADR 0004 — Parser XLSX bằng openpyxl

## Trạng thái

Chấp nhận.

## Quyết định

Dùng `openpyxl` cho parser tham chiếu M1. Chế độ chỉ đọc duyệt từng hàng, giữ tên sheet và số dòng. Chỉ dùng giá trị công thức đã lưu trong workbook và bỏ external links.

Đọc ZIP/XML thủ công sẽ phải tự xử lý shared strings, kiểu ô và định dạng workbook. Calamine thuộc mốc M3, sau khi có golden test và số đo đối chiếu.
