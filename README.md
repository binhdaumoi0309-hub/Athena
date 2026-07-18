# HeartCare AI - Trợ lý AI Chăm sóc Khách hàng Bệnh viện Tim Hà Nội

> Nền tảng chăm sóc khách hàng thông minh, hỗ trợ người bệnh tiếp cận thông tin bệnh viện nhanh chóng, chính xác và thuận tiện.

## Giới thiệu

Trong quá trình tìm hiểu và sử dụng dịch vụ y tế, người bệnh thường gặp nhiều khó khăn như:

- Không biết nên khám ở khoa nào.
- Mất nhiều thời gian tìm kiếm thông tin trên website.
- Không rõ chi phí khám và các dịch vụ.
- Khó lựa chọn bác sĩ phù hợp.
- Chưa nắm được quy trình khám bệnh.
- Không biết khi nào cần đến cấp cứu.

Dự án **Trợ lý AI Chăm sóc Khách hàng Bệnh viện Tim Hà Nội** được xây dựng nhằm giải quyết những vấn đề trên bằng một trợ lý AI chăm sóc khách hàng hiện đại, giúp người bệnh tiếp cận thông tin y tế nhanh chóng, chính xác và thuận tiện; đồng thời hỗ trợ bệnh viện nâng cao chất lượng dịch vụ và thúc đẩy quá trình chuyển đổi số trong lĩnh vực chăm sóc sức khỏe.

---

# Các chức năng nổi bật

## 🤖 Trợ lý AI thông minh

Người dùng có thể đặt câu hỏi bằng ngôn ngữ tự nhiên như:

- "Siêu âm tim giá bao nhiêu?"
- "Tôi muốn đặt lịch khám tim mạch."
- "Bác sĩ nào chuyên điều trị rối loạn nhịp tim?"
- "Tôi cần mang những giấy tờ gì khi khám?"

AI sẽ phân tích yêu cầu và trả lời bằng thông tin phù hợp, dễ hiểu.

---

## 🏥 Tra cứu thông tin bệnh viện

Hỗ trợ tra cứu nhanh:

- Chuyên khoa
- Bác sĩ
- Dịch vụ khám chữa bệnh
- Quy trình khám
- Hướng dẫn dành cho người bệnh
- Các câu hỏi thường gặp

Thay vì phải tìm kiếm trên nhiều trang khác nhau, người dùng chỉ cần trò chuyện với AI.

---

## 💰 Tra cứu bảng giá dịch vụ

Người bệnh có thể tra cứu nhanh chi phí của các dịch vụ như:

- Khám chuyên khoa
- Điện tim
- Siêu âm tim
- Xét nghiệm
- Chẩn đoán hình ảnh

Thông tin được lấy từ dữ liệu của bệnh viện, giúp người bệnh chủ động chuẩn bị chi phí trước khi đến khám.

---

## 📅 Hỗ trợ đặt lịch khám

Hệ thống hỗ trợ:

- Xem lịch khám
- Tìm bác sĩ phù hợp
- Gửi yêu cầu đặt lịch
- Hướng dẫn quy trình khám

Giúp giảm thời gian chờ và đơn giản hóa quá trình đăng ký khám.

---

## 🚨 Hướng dẫn trong tình huống khẩn cấp

Đối với các triệu chứng nguy hiểm như:

- Đau ngực kéo dài
- Khó thở nghiêm trọng
- Ngất
- Mất ý thức

Hệ thống sẽ ưu tiên khuyến nghị người bệnh đến cơ sở y tế gần nhất hoặc gọi cấp cứu thay vì tiếp tục tư vấn.

An toàn của người bệnh luôn được đặt lên hàng đầu.

---

# Hành trình người bệnh

Hệ thống hỗ trợ người bệnh xuyên suốt quá trình khám chữa bệnh.

```
Tìm hiểu thông tin
        ↓
Trao đổi với AI
        ↓
Nhận hướng dẫn phù hợp
        ↓
Lựa chọn chuyên khoa
        ↓
Chọn bác sĩ
        ↓
Đặt lịch khám
        ↓
Đến bệnh viện
```

---


# Cơ sở tri thức

Để đảm bảo câu trả lời đáng tin cậy, AI không chỉ dựa trên mô hình ngôn ngữ mà còn khai thác dữ liệu từ kho tri thức của bệnh viện.

Nguồn dữ liệu bao gồm:

- Website chính thức của bệnh viện
- Bảng giá dịch vụ
- Quy trình khám chữa bệnh
- Tài liệu chính thống của bệnh viện
- Hình ảnh và tài liệu đã được OCR

Dữ liệu được lập chỉ mục bằng **Vector Search**, cho phép AI tìm kiếm theo ngữ nghĩa và đưa ra câu trả lời sát với nội dung người dùng cần.

---

# Lợi ích mang lại

## Đối với người bệnh

- Tiếp cận thông tin nhanh chóng
- Hỗ trợ 24/7
- Giảm thời gian tìm kiếm thông tin
- Dễ dàng đặt lịch khám
- Hiểu rõ quy trình khám chữa bệnh
- Chủ động chuẩn bị trước khi đến bệnh viện

## Đối với bệnh viện

- Giảm tải cho bộ phận chăm sóc khách hàng
- Chuẩn hóa thông tin cung cấp cho người bệnh
- Nâng cao trải nghiệm người dùng
- Hỗ trợ chuyển đổi số trong lĩnh vực y tế
- Tăng hiệu quả vận hành

---

# Công nghệ sử dụng

- Google Agent Development Kit (Google ADK)
- Python
- FastAPI
- React
- TypeScript
- Vite
- Firebase
- Firestore
- Firestore Vector Search
