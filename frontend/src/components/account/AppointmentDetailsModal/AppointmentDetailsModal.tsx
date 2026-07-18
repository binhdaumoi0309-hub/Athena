import { useEffect, useRef, useState } from 'react';
import {
  CalendarDays,
  Clock3,
  Download,
  HeartPulse,
  MapPin,
  Phone,
  Stethoscope,
  UserRound,
  X,
} from 'lucide-react';
import type { Appointment } from '../../../types';
import styles from './AppointmentDetailsModal.module.css';

interface AppointmentDetailsModalProps {
  appointment: Appointment;
  onClose: () => void;
}

function genderLabel(value?: string): string {
  if (value === 'male') return 'Nam';
  if (value === 'female') return 'Nữ';
  return value || 'Chưa cập nhật';
}

function shiftLabel(appointment: Appointment): string {
  if (appointment.shift === 'morning') return 'Buổi sáng';
  if (appointment.shift === 'afternoon') return 'Buổi chiều';
  return appointment.time;
}

export function AppointmentDetailsModal({
  appointment,
  onClose,
}: AppointmentDetailsModalProps) {
  const receiptRef = useRef<HTMLDivElement>(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [onClose]);

  const patientSummary = [
    appointment.patientName,
    appointment.patientCccd ? `CCCD: ${appointment.patientCccd}` : null,
    appointment.patientPhone ? `SĐT: ${appointment.patientPhone}` : null,
    appointment.patientDob ? `Ngày sinh: ${appointment.patientDob}` : null,
    `Giới tính: ${genderLabel(appointment.patientGender)}`,
    appointment.patientAddress ? `Địa chỉ: ${appointment.patientAddress}` : null,
    appointment.patientHometown ? `Quê quán: ${appointment.patientHometown}` : null,
  ].filter(Boolean).join(', ');

  const downloadPdf = async () => {
    if (!receiptRef.current || downloading) return;
    setDownloading(true);
    try {
      await document.fonts.ready;
      const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
        import('html2canvas'),
        import('jspdf'),
      ]);
      const canvas = await html2canvas(receiptRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false,
      });
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 12;
      const availableWidth = pageWidth - margin * 2;
      const availableHeight = pageHeight - margin * 2;
      const imageRatio = canvas.height / canvas.width;
      let imageWidth = availableWidth;
      let imageHeight = imageWidth * imageRatio;
      if (imageHeight > availableHeight) {
        imageHeight = availableHeight;
        imageWidth = imageHeight / imageRatio;
      }
      const imageX = (pageWidth - imageWidth) / 2;
      pdf.addImage(
        canvas.toDataURL('image/png'),
        'PNG',
        imageX,
        margin,
        imageWidth,
        imageHeight,
        undefined,
        'FAST',
      );
      pdf.save(`phieu-lich-kham-${appointment.code}.pdf`);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div
      className={styles.overlay}
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="appointment-details-title"
      >
        <button className={styles.closeButton} type="button" onClick={onClose} aria-label="Đóng">
          <X />
        </button>

        <div className={styles.receipt} ref={receiptRef}>
          <header className={styles.receiptHeader}>
            <img src="/logos/hanoi-heart-hospital.svg" alt="" width="58" height="58" />
            <div>
              <p>Bệnh viện Tim Hà Nội</p>
              <h2 id="appointment-details-title">Phiếu thông tin lịch khám</h2>
            </div>
            <HeartPulse aria-hidden="true" />
          </header>

          <div className={styles.codeRow}>
            <span>Mã đặt khám</span>
            <strong>{appointment.code}</strong>
          </div>

          <div className={styles.detailsGrid}>
            <article>
              <CalendarDays />
              <span>Ngày khám</span>
              <strong>{appointment.date}</strong>
            </article>
            <article>
              <Clock3 />
              <span>Buổi khám</span>
              <strong>{shiftLabel(appointment)}</strong>
            </article>
            <article>
              <Stethoscope />
              <span>Bác sĩ</span>
              <strong>{appointment.doctorName}</strong>
            </article>
            <article>
              <MapPin />
              <span>Địa điểm</span>
              <strong>{appointment.facilityName}</strong>
            </article>
            <article>
              <Phone />
              <span>Số điện thoại hỗ trợ</span>
              <strong>024 3942 2430</strong>
            </article>
          </div>

          <section className={styles.patientSection}>
            <h3><UserRound /> Thông tin người khám</h3>
            <p>{patientSummary}</p>
          </section>

          {appointment.symptoms && (
            <section className={styles.symptomsSection}>
              <h3>Triệu chứng</h3>
              <p>{appointment.symptoms}</p>
            </section>
          )}

          <footer className={styles.receiptFooter}>
            <strong>Lưu ý khi đến khám</strong>
            <p>Vui lòng có mặt trước giờ hẹn 15 phút và mang theo giấy tờ tùy thân, thẻ BHYT nếu có.</p>
          </footer>
        </div>

        <div className={styles.actions}>
          <button type="button" onClick={() => void downloadPdf()} disabled={downloading}>
            <Download /> {downloading ? 'Đang tạo PDF...' : 'Tải xuống'}
          </button>
          <button type="button" onClick={onClose}>Đóng</button>
        </div>
      </section>
    </div>
  );
}
