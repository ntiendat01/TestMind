# Checkout

## Mã giảm giá

REQ-101. Chỉ dùng một mã giảm giá cho mỗi đơn. Khi mã hết hạn, checkout phải báo lỗi và giữ nguyên giỏ hàng.

## Giao dịch trùng

REQ-102. Nếu nhận lại cùng khóa idempotency với cùng nội dung, API trả về kết quả của lần thử đầu và không tạo đơn mới.

## Thanh toán chờ xác nhận

REQ-103. Nếu chưa nhận xác nhận thanh toán, đơn hiển thị Đang chờ và hệ thống giữ hàng 15 phút. Hết thời hạn mà giao dịch vẫn chưa xác nhận thì hết giữ hàng và đơn chuyển sang Hết hạn.

## Phí vận chuyển

REQ-104. Phí vận chuyển được tính lại sau khi khách đổi địa chỉ. Checkout hiển thị tổng mới trước khi khách xác nhận.
