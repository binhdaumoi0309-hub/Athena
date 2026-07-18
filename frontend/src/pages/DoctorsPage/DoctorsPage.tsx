import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { DoctorCard } from '../../components/common/DoctorCard';
import { DoctorProfileModal } from '../../components/common/DoctorProfileModal';
import { PageHero } from '../../components/common/PageHero';
import { StatePanel } from '../../components/common/StatePanel';
import { doctorService } from '../../services';
import type { Doctor } from '../../types';
import styles from './DoctorsPage.module.css';

const INITIAL_DOCTOR_COUNT = 4;
const LOAD_MORE_COUNT = 8;

function normalizeSearch(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLocaleLowerCase('vi');
}

export function DoctorsPage() {
  const [query, setQuery] = useState('');
  const [visibleCount, setVisibleCount] = useState(INITIAL_DOCTOR_COUNT);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const doctors = useQuery({
    queryKey: ['doctor-capabilities'],
    queryFn: doctorService.list,
  });

  const filteredDoctors = useMemo(() => {
    const normalizedQuery = normalizeSearch(query.trim());
    if (!normalizedQuery) return doctors.data ?? [];
    return (doctors.data ?? []).filter((doctor) =>
      normalizeSearch(doctor.name).includes(normalizedQuery),
    );
  }, [doctors.data, query]);

  const visibleDoctors = filteredDoctors.slice(0, visibleCount);
  const hasMore = visibleCount < filteredDoctors.length;

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
                onChange={(event) => {
                  setQuery(event.target.value);
                  setVisibleCount(INITIAL_DOCTOR_COUNT);
                }}
                placeholder="Nhập tên bác sĩ"
              />
            </label>
          </div>

          {doctors.isLoading ? (
            <StatePanel kind="loading" />
          ) : doctors.isError ? (
            <StatePanel
              kind="error"
              description="Không thể tải dữ liệu bác sĩ từ hệ thống."
              onRetry={() => void doctors.refetch()}
            />
          ) : filteredDoctors.length === 0 ? (
            <StatePanel
              kind="empty"
              title="Không tìm thấy bác sĩ"
              description="Hãy kiểm tra lại tên bác sĩ bạn muốn tìm."
            />
          ) : (
            <>
              <p className={styles.count}>
                Hiện có <strong>{filteredDoctors.length}</strong> bác sĩ
              </p>
              <div className={styles.grid}>
                {visibleDoctors.map((doctor) => (
                  <DoctorCard key={doctor.id} doctor={doctor} onViewProfile={setSelectedDoctor} />
                ))}
              </div>
              {hasMore && (
                <div className={styles.loadMoreWrapper}>
                  <button
                    className={styles.loadMoreButton}
                    type="button"
                    onClick={() => setVisibleCount((count) => count + LOAD_MORE_COUNT)}
                  >
                    Xem thêm
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
      {selectedDoctor && (
        <DoctorProfileModal doctor={selectedDoctor} onClose={() => setSelectedDoctor(null)} />
      )}
    </>
  );
}
