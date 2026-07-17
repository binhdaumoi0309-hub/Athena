import { useMemo, useState } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { DoctorCard } from '../../components/common/DoctorCard';
import { PageHero } from '../../components/common/PageHero';
import { StatePanel } from '../../components/common/StatePanel';
import { doctorService } from '../../services';
import styles from './DoctorsPage.module.css';

export function DoctorsPage() {
  const [query, setQuery] = useState('');
  const [specialty, setSpecialty] = useState('');
  const doctors = useQuery({
    queryKey: ['doctors'],
    queryFn: () => doctorService.list(),
  });
  const specialties = useQuery({
    queryKey: ['specialties'],
    queryFn: doctorService.specialties,
  });
  const filteredDoctors = useMemo(
    () =>
      doctors.data?.filter(
        (doctor) =>
          (!specialty || doctor.specialtyId === specialty) &&
          `${doctor.title} ${doctor.name} ${doctor.specialty}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ) ?? [],
    [doctors.data, query, specialty],
  );

  return (
    <>
      <PageHero
        simple
        title="Đội ngũ bác sĩ"
        description="Thông tin đội ngũ bác sĩ và chuyên gia tim mạch đang công tác tại bệnh viện. Hồ sơ chi tiết sẽ được cập nhật theo dữ liệu chính thức."
      />
      <section className="section section-soft">
        <div className="container">
          <div className={styles.filters}>
            <label>
              <span className="sr-only">Tìm theo tên bác sĩ</span>
              <Search size={19} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Nhập tên bác sĩ hoặc chuyên khoa"
              />
            </label>
            <label>
              <SlidersHorizontal size={18} />
              <span className="sr-only">Lọc theo chuyên khoa</span>
              <select
                value={specialty}
                onChange={(event) => setSpecialty(event.target.value)}
              >
                <option value="">Tất cả chuyên khoa</option>
                {specialties.data?.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {doctors.isLoading ? (
            <StatePanel kind="loading" />
          ) : doctors.isError ? (
            <StatePanel kind="error" onRetry={() => void doctors.refetch()} />
          ) : filteredDoctors.length === 0 ? (
            <StatePanel
              kind="empty"
              title="Không tìm thấy bác sĩ"
              description="Hãy thử từ khóa hoặc chuyên khoa khác."
            />
          ) : (
            <>
              <p className={styles.count}>
                Hiện có <strong>{filteredDoctors.length}</strong> bác sĩ
              </p>
              <div className={styles.grid}>
                {filteredDoctors.map((doctor) => (
                  <DoctorCard key={doctor.id} doctor={doctor} />
                ))}
              </div>
            </>
          )}
        </div>
      </section>
    </>
  );
}
