import { useState } from 'react';
import { CalendarDays, Clock, Filter } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { PageHero } from '../../components/common/PageHero';
import { StatePanel } from '../../components/common/StatePanel';
import { AppointmentList } from '../../components/account/AppointmentList';
import { appointmentService, authService, scheduleService } from '../../services';
import styles from './SchedulePage.module.css';

export function SchedulePage() {
  const [doctorId, setDoctorId] = useState('');
  const doctors = useQuery({
    queryKey: ['booking-doctors', 'all'],
    queryFn: () => scheduleService.doctors(''),
  });
  const schedule = useQuery({
    queryKey: ['schedule', doctorId],
    queryFn: () => scheduleService.list(doctorId),
  });
  const appointments = useQuery({
    queryKey: ['appointments'],
    queryFn: appointmentService.list,
    enabled: authService.isAuthenticated(),
    refetchOnMount: 'always',
  });

  return (
    <>
      <PageHero
        simple
        title="Lịch khám"
        description="Tra cứu lịch làm việc và các khung giờ còn trống của bác sĩ trong những ngày tới."
      />
      <section className="section">
        <div className="container">
          <div className={styles.myAppointments}>
            <h2>Lịch khám của bạn</h2>
            {appointments.isLoading ? (
              <StatePanel kind="loading" title="Đang tải lịch khám của bạn" />
            ) : appointments.isError ? (
              <StatePanel
                kind="error"
                title="Không thể tải lịch khám của bạn"
                onRetry={() => void appointments.refetch()}
              />
            ) : appointments.data?.length ? (
              <AppointmentList appointments={appointments.data} />
            ) : (
              <p className={styles.emptyAppointments}>Bạn không có lịch khám nào.</p>
            )}
          </div>

          <h2 className={styles.lookupTitle}>Tra cứu lịch còn chỗ</h2>
          <div className={styles.filter}>
            <Filter size={19} />
            <label htmlFor="schedule-doctor">Chọn bác sĩ</label>
            <select
              id="schedule-doctor"
              value={doctorId}
              onChange={(event) => setDoctorId(event.target.value)}
            >
              <option value="">Tất cả bác sĩ</option>
              {doctors.data?.map((doctor) => (
                <option key={doctor.name} value={doctor.name}>
                  {doctor.name}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.legend}>
            <span><i className={styles.available} />Còn chỗ</span>
            <span><i className={styles.full} />Hết lịch</span>
            <span><i className={styles.booked} />Vừa có người đặt</span>
          </div>

          {schedule.isLoading ? (
            <StatePanel kind="loading" />
          ) : schedule.isError ? (
            <StatePanel
              kind="offline"
              description="Không thể tải lịch khám. Vui lòng kiểm tra kết nối."
              onRetry={() => void schedule.refetch()}
            />
          ) : (
            <div className={styles.grid}>
              {schedule.data?.map((day) => (
                <article key={day.date}>
                  <h2><CalendarDays size={19} />{day.label}</h2>
                  <div>
                    {day.slots.map((slot) => (
                      <Link
                        aria-disabled={slot.status !== 'available'}
                        className={styles[slot.status]}
                        key={slot.id}
                        to={
                          slot.status === 'available'
                            ? `/dat-lich?date=${day.date}&time=${slot.time}`
                            : '#'
                        }
                      >
                        <Clock size={14} />
                        {slot.label ?? slot.time}
                        <small>
                          {slot.status === 'full'
                            ? 'Hết lịch'
                            : slot.status === 'just_booked'
                              ? 'Vừa đặt'
                              : typeof slot.remaining_capacity === 'number'
                                ? `Còn ${slot.remaining_capacity} chỗ`
                                : 'Còn chỗ'}
                        </small>
                      </Link>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
