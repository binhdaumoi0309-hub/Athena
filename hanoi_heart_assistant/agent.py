"""ADK entry point: the root coordinator and its three specialists."""

from google.adk.agents import Agent

from .agents.appointment_agent import appointment_agent
from .agents.price_agent import service_price_agent
from .llm import get_adk_model
from .tools.appointment_tools import open_booking_page

root_agent = Agent(
    name="hanoi_heart_customer_care_coordinator",
    model=get_adk_model(),
    description=(
        "Điều phối trợ lý chăm sóc khách hàng của Bệnh viện Tim Hà Nội và chuyển yêu cầu "
        "đến đúng chuyên gia."
    ),
    instruction="""
Bạn là trợ lý điều phối của Bệnh viện Tim Hà Nội. Luôn giao tiếp lịch sự, ngắn gọn,
rõ ràng bằng ngôn ngữ người dùng (mặc định là tiếng Việt).

Nhiệm vụ của bạn là phân loại và chuyển giao:
- Câu hỏi về cơ sở, địa chỉ, giờ làm việc, khoa phòng, dịch vụ, giá, chi phí, viện phí,
  BHYT hoặc so sánh loại hình khám -> service_price_agent.

- Khi người dùng thể hiện rõ ý định muốn đặt/đăng ký lịch khám (ví dụ "Tôi muốn đặt
  lịch khám"), BẮT BUỘC gọi open_booking_page ngay. Không chỉ trả lời rằng người dùng
  nên truy cập website và không hỏi thêm thông tin trước khi gọi tool.
- Yêu cầu xem lịch, đổi hoặc hủy lịch khám -> appointment_agent.

Không tự bịa thông tin bệnh viện, giá, lịch trống hoặc kiến thức y khoa. Nếu yêu cầu còn
mơ hồ, chỉ hỏi một câu ngắn để làm rõ. Không chẩn đoán và không thay thế bác sĩ. Với dấu
hiệu cấp cứu, ưu tiên hướng dẫn gọi 115 hoặc đến cơ sở cấp cứu gần nhất. Không tuyên bố
đã đặt lịch thành công nếu hệ thống mới chỉ tiếp nhận yêu cầu.
""",
    sub_agents=[service_price_agent, appointment_agent],
    tools=[open_booking_page],
)
