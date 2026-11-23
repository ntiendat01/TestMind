# Hoàn tiền

## Hạn gửi yêu cầu

REQ-045. Khách có thể yêu cầu hoàn tiền toàn phần trong 7 ngày lịch kể từ lúc xác nhận thanh toán. Điều kiện là đơn chưa được bàn giao cho đơn vị vận chuyển.

## Phương thức hoàn

REQ-046. Tiền được trả về cùng phương thức đã dùng để thanh toán. Thanh toán bằng hai phương thức được phân bổ theo số tiền ban đầu của từng phương thức.

## Hàng đã giao

REQ-047. Nếu giao hàng sai hoặc hàng bị hỏng, khách có thể mở yêu cầu kiểm tra trong 48 giờ từ lúc giao. Bộ phận hỗ trợ cần ảnh nhãn vận chuyển và ảnh sản phẩm. Đơn hợp lệ chuyển sang quy trình trả hàng.

## Trạng thái hoàn tiền

REQ-048. Khi nhà cung cấp thanh toán chấp nhận yêu cầu hoàn, trạng thái hiển thị là Đang xử lý. Sau khi nhận xác nhận hoàn tất, trạng thái chuyển sang Đã hoàn. Nếu bên thanh toán báo lỗi, yêu cầu chuyển sang Cần hỗ trợ.
