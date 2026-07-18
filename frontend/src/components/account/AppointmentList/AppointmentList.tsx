import { useState } from 'react';
import { CalendarDays, Clock3, MapPin } from 'lucide-react';
import type { Appointment } from '../../../types';
import { AppointmentDetailsModal } from '../AppointmentDetailsModal';
import styles from './AppointmentList.module.css';

const statusLabels = {
  upcoming: 'Sắp tới',
  completed: 'Đã khám',
  cancelled: 'Đã hủy',
};

export function AppointmentList({ appointments }: { appointments: Appointment[] }) {
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

  return (
    <>
      <div className={styles.list}>
        {appointments.map((appointment) => (
          <article key={appointment.id}>
            <header>
              <strong>{appointment.code}</strong>
              <span className={styles[appointment.status]}>
                {statusLabels[appointment.status]}
              </span>
            </header>

            <div className={styles.titleRow}>
              <h2>{appointment.doctorName}</h2>
              <div className={styles.actions}>
                <button type="button" onClick={() => setSelectedAppointment(appointment)}>
                  Xem thông tin
                </button>
                {appointment.status === 'upcoming' && (
                  <button type="button">Hủy lịch</button>
                )}
              </div>
            </div>

            <div className={styles.meta}>
              <span><CalendarDays />{appointment.date}</span>
              <span><Clock3 />{appointment.shift === 'morning' ? 'Buổi sáng' : appointment.shift === 'afternoon' ? 'Buổi chiều' : appointment.time}</span>
              <span><MapPin />{appointment.facilityName}</span>
            </div>
          </article>
        ))}
      </div>

      {selectedAppointment && (
        <AppointmentDetailsModal
          appointment={selectedAppointment}
          onClose={() => setSelectedAppointment(null)}
        />
      )}
    </>
  );
}
