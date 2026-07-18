import { CalendarDays } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Doctor } from '../../../types';
import styles from './DoctorCard.module.css';

interface DoctorCardProps {
  doctor: Doctor;
  onViewProfile: (doctor: Doctor) => void;
}

export function DoctorCard({ doctor, onViewProfile }: DoctorCardProps) {
  return (
    <article className={styles.card}>
      <div className={styles.content}>
        <h2>{doctor.name}</h2>
        <p className={styles.about}>{doctor.about || 'Thông tin bác sĩ đang được cập nhật.'}</p>
        <div className={styles.actions}>
          <button type="button" onClick={() => onViewProfile(doctor)}>Xem hồ sơ</button>
          <Link to="/dat-lich"><CalendarDays size={16} />Đặt lịch</Link>
        </div>
      </div>
    </article>
  );
}
