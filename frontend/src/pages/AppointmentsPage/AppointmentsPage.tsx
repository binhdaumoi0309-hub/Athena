import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AccountLayout } from '../../components/account/AccountLayout';
import { AppointmentList } from '../../components/account/AppointmentList';
import { StatePanel } from '../../components/common/StatePanel';
import { appointmentService } from '../../services';
import styles from './AppointmentsPage.module.css';

const filters = [
  ['all', 'Tất cả'],
  ['upcoming', 'Sắp tới'],
  ['completed', 'Đã khám'],
  ['cancelled', 'Đã hủy'],
] as const;

export function AppointmentsPage() {
  const [filter, setFilter] = useState('all');
  const query = useQuery({
    queryKey: ['appointments'],
    queryFn: appointmentService.list,
    refetchOnMount: 'always',
  });
  const appointments = query.data?.filter(
    (item) => filter === 'all' || item.status === filter,
  ) ?? [];

  return (
    <AccountLayout title="Quản lý lịch hẹn">
      <div className={styles.tabs}>
        {filters.map(([value, label]) => (
          <button
            className={filter === value ? styles.active : undefined}
            key={value}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
      </div>
      {query.isLoading ? (
        <StatePanel kind="loading" />
      ) : query.isError ? (
        <StatePanel
          kind="error"
          title="Không thể tải lịch hẹn"
          onRetry={() => void query.refetch()}
        />
      ) : appointments.length === 0 ? (
        <p className={styles.emptyText}>Bạn không có lịch khám nào.</p>
      ) : (
        <AppointmentList appointments={appointments} />
      )}
    </AccountLayout>
  );
}
