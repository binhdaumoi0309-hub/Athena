import { useEffect, useRef } from 'react';
import { CalendarDays, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Doctor } from '../../../types';
import styles from './DoctorProfileModal.module.css';

interface DoctorProfileModalProps {
  doctor: Doctor;
  onClose: () => void;
}

export function DoctorProfileModal({ doctor, onClose }: DoctorProfileModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    closeButtonRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [onClose]);

  return (
    <div
      className={styles.backdrop}
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="doctor-profile-title"
      >
        <header>
          <div>
            <span>Thông tin bác sĩ</span>
            <h2 id="doctor-profile-title">{doctor.name}</h2>
          </div>
          <button ref={closeButtonRef} type="button" onClick={onClose} aria-label="Đóng thông tin bác sĩ">
            <X size={21} />
          </button>
        </header>

        <div className={styles.content}>
          <h3>Mô tả</h3>
          <p>{doctor.about || 'Thông tin bác sĩ đang được cập nhật.'}</p>
        </div>

        <footer>
          <button type="button" onClick={onClose}>Đóng</button>
          <Link to="/dat-lich" onClick={onClose}>
            <CalendarDays size={17} /> Đặt lịch khám
          </Link>
        </footer>
      </section>
    </div>
  );
}
