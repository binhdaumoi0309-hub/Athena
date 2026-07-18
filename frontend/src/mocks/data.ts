import type { Appointment, Doctor, Facility, PriceItem, ScheduleDay, Specialty } from '../types';

export const facilities: Facility[] = [
  { id: 'cs1', name: 'Bệnh viện Tim Hà Nội — Cơ sở 1', shortName: 'Cơ sở 1', address: 'Số 92 Trần Hưng Đạo, phường Cửa Nam, Hà Nội', phone: '19001082', hours: '07:00–17:00', image: '/images/hospital-campus.svg' },
  { id: 'cs2', name: 'Bệnh viện Tim Hà Nội — Cơ sở 2', shortName: 'Cơ sở 2', address: 'Số 695 Lạc Long Quân, phường Tây Hồ, Hà Nội', phone: '19001082', hours: '07:00–17:00', image: '/images/hospital-building.svg' },
];

export const specialties: Specialty[] = [
  { id: 'intervention', name: 'Tim mạch can thiệp', description: 'Chẩn đoán, can thiệp mạch vành và bệnh tim cấu trúc.', icon: 'activity', doctorCount: 12 },
  { id: 'surgery', name: 'Phẫu thuật tim', description: 'Phẫu thuật tim hở, van tim và mạch máu lớn.', icon: 'heart-pulse', doctorCount: 9 },
  { id: 'rhythm', name: 'Rối loạn nhịp', description: 'Điện sinh lý, triệt đốt và máy tạo nhịp.', icon: 'waves', doctorCount: 7 },
  { id: 'general', name: 'Tim mạch tổng quát', description: 'Khám, tầm soát và quản lý bệnh tim mạch.', icon: 'stethoscope', doctorCount: 18 },
  { id: 'pediatric', name: 'Tim mạch nhi', description: 'Chăm sóc bệnh tim bẩm sinh ở trẻ em.', icon: 'baby', doctorCount: 6 },
  { id: 'imaging', name: 'Chẩn đoán hình ảnh', description: 'Siêu âm tim, CT và MRI tim mạch.', icon: 'scan-line', doctorCount: 10 },
];

const doctorImages = ['/images/doctor-nguyen-van-manh.svg','/images/doctor-tran-thi-lan.svg','/images/doctor-pham-minh-khoa.svg','/images/doctor-le-thi-huong.svg','/images/doctor-dang-quoc-tuan.svg','/images/doctor-nguyen-thu-ha.svg'];
export const doctors: Doctor[] = [
  ['nguyen-van-manh','Nguyễn Văn Mạnh','GS.TS.','intervention','Tim mạch can thiệp',30,4.9,234,'cs1'],
  ['tran-thi-lan','Trần Thị Lan','PGS.TS.','surgery','Phẫu thuật tim',25,4.8,189,'cs2'],
  ['pham-minh-khoa','Phạm Minh Khoa','TS.','rhythm','Rối loạn nhịp',18,4.7,156,'cs1'],
  ['le-thi-huong','Lê Thị Hương','BSCKII.','general','Tim mạch tổng quát',20,4.9,312,'cs2'],
  ['dang-quoc-tuan','Đặng Quốc Tuấn','PGS.TS.','intervention','Tim mạch can thiệp',22,4.8,267,'cs1'],
  ['nguyen-thu-ha','Nguyễn Thu Hà','BSCKI.','pediatric','Tim mạch nhi',15,4.6,98,'cs2'],
].map((d, index) => ({ id: d[0] as string, name: d[1] as string, title: d[2] as string, specialtyId: d[3] as string, specialty: d[4] as string, experience: d[5] as number, rating: d[6] as number, reviews: d[7] as number, facilityId: d[8] as string, image: doctorImages[index], languages: ['Tiếng Việt', 'English'], education: ['Đại học Y Hà Nội', 'Đào tạo chuyên sâu tim mạch'], about: 'Bác sĩ có nhiều năm kinh nghiệm trong chẩn đoán và điều trị bệnh lý tim mạch, luôn đặt an toàn và trải nghiệm người bệnh lên hàng đầu.' }));

const times = ['07:30','08:00','08:30','09:00','09:30','10:00','13:30','14:00','14:30','15:00'];
export const schedules: ScheduleDay[] = Array.from({ length: 6 }, (_, i) => {
  const date = new Date(2026, 6, 20 + i);
  return { date: date.toISOString().slice(0, 10), label: new Intl.DateTimeFormat('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit' }).format(date), slots: times.map((time, j) => ({ id: `${i}-${j}`, time, status: j === 2 ? 'full' : j === 6 ? 'just_booked' : 'available' })) };
});

export const prices: PriceItem[] = [
  { id: 'p1', category: 'Khám bệnh', service: 'Khám tim mạch chuyên khoa', code: 'KB-TM01', price: 250000, insurance: true },
  { id: 'p2', category: 'Khám bệnh', service: 'Khám Giáo sư/Phó Giáo sư', code: 'KB-TM02', price: 500000, insurance: false },
  { id: 'p3', category: 'Chẩn đoán', service: 'Điện tâm đồ thường', code: 'CD-TM01', price: 120000, insurance: true },
  { id: 'p4', category: 'Chẩn đoán', service: 'Siêu âm tim Doppler màu', code: 'CD-TM02', price: 450000, insurance: true },
  { id: 'p5', category: 'Xét nghiệm', service: 'Bộ xét nghiệm tim mạch cơ bản', code: 'XN-TM01', price: 680000, insurance: true },
  { id: 'p6', category: 'Can thiệp', service: 'Chụp động mạch vành', code: 'CT-TM01', price: 5200000, insurance: true },
];

export const appointments: Appointment[] = [
  { id: 'a1', code: 'BVT-260720-1842', doctorName: 'GS.TS. Nguyễn Văn Mạnh', specialty: 'Tim mạch can thiệp', facilityName: 'Cơ sở 1', date: '2026-07-20', time: '08:30', status: 'upcoming', patientName: 'Nguyễn Minh Anh' },
  { id: 'a2', code: 'BVT-260602-0911', doctorName: 'BSCKII. Lê Thị Hương', specialty: 'Tim mạch tổng quát', facilityName: 'Cơ sở 2', date: '2026-06-02', time: '14:00', status: 'completed', patientName: 'Nguyễn Minh Anh' },
];
