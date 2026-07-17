import { useState } from 'react';
import { CalendarDays, Clock, Filter } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { PageHero } from '../../components/common/PageHero';
import { StatePanel } from '../../components/common/StatePanel';
import { doctorService, scheduleService } from '../../services';
import styles from './SchedulePage.module.css';

export function SchedulePage() {
  const [doctorId, setDoctorId] = useState('');
  const doctors = useQuery({
    queryKey: ['doctors'],
    queryFn: () => doctorService.list(),
  });
  const schedule = useQuery({
    queryKey: ['schedule', doctorId],
    queryFn: () => scheduleService.list(doctorId),
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
                <option key={doctor.id} value={doctor.id}>
                  {doctor.title} {doctor.name}
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
                        {slot.time}
                        <small>
                          {slot.status === 'full'
                            ? 'Hết lịch'
                            : slot.status === 'just_booked'
                              ? 'Vừa đặt'
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
