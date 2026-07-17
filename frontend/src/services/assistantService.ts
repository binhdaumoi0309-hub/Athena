import { doctors, prices, schedules } from '../mocks/data';
import type { AssistantMessage, AssistantIntent } from '../types';
import { apiClient, mockDelay } from './apiClient';

const detectIntent = (text: string): AssistantIntent => {
  const value = text.toLowerCase();
  if (/đau ngực|khó thở|ngất|cấp cứu/.test(value)) return 'emergency';
  if (/bác sĩ|chuyên gia/.test(value)) return 'find_doctor';
  if (/lịch|giờ|đặt khám/.test(value)) return 'schedule';
  if (/giá|chi phí|bhyt/.test(value)) return 'pricing';
  if (/chuẩn bị|hướng dẫn/.test(value)) return 'guide';
  return 'general';
};

export const assistantService = {
  send: async (text: string): Promise<AssistantMessage> => {
    if (!apiClient.useMocks) return apiClient.post('/assistant/messages', { message: text });
    const intent = detectIntent(text);
    const emergency = intent === 'emergency';
    const answers: Record<AssistantIntent, string> = {
      emergency: 'Các triệu chứng bạn mô tả có thể là dấu hiệu cấp cứu tim mạch. Hãy gọi 115 ngay hoặc đến cơ sở y tế gần nhất. Không tự lái xe.',
      find_doctor: 'Dưới đây là các bác sĩ tim mạch phù hợp. Bạn có thể xem hồ sơ hoặc đặt lịch trực tiếp.',
      schedule: 'Mình đã tìm thấy một số lịch khám gần nhất còn chỗ.',
      pricing: 'Dưới đây là giá tham khảo. Chi phí thực tế có thể thay đổi theo chỉ định và quyền lợi BHYT.',
      guide: 'Bạn nên chuẩn bị các giấy tờ và thông tin dưới đây trước khi đến khám.',
      general: 'Mình có thể giúp bạn tìm bác sĩ, tra lịch, xem bảng giá, hướng dẫn BHYT hoặc đặt lịch khám.',
    };
    return mockDelay({ id: crypto.randomUUID(), role: 'assistant', intent, answer: answers[intent], emergency, actions: emergency ? [{ id: 'call', label: 'Gọi 115', href: 'tel:115' }] : [{ id: 'book', label: 'Đặt lịch khám', href: '/dat-lich' }], structured_data: { doctors: intent === 'find_doctor' ? doctors.slice(0, 2) : undefined, schedules: intent === 'schedule' ? schedules.slice(0, 2) : undefined, prices: intent === 'pricing' ? prices.slice(0, 3) : undefined, checklist: intent === 'guide' ? ['CCCD hoặc giấy tờ tùy thân', 'Thẻ BHYT và giấy chuyển tuyến (nếu có)', 'Đơn thuốc, kết quả xét nghiệm cũ', 'Nhịn ăn nếu được chỉ định trước'] : undefined }, citations: [] }, 700);
  },
};
