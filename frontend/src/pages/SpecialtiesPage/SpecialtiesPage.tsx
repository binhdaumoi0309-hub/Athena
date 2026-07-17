import {
  Activity,
  ArrowRight,
  Baby,
  HeartPulse,
  ScanLine,
  Stethoscope,
  Waves,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { PageHero } from '../../components/common/PageHero';
import { StatePanel } from '../../components/common/StatePanel';
import { doctorService } from '../../services';
import styles from './SpecialtiesPage.module.css';

const specialtyIcons = [Activity, HeartPulse, Waves, Stethoscope, Baby, ScanLine];

export function SpecialtiesPage() {
  const specialties = useQuery({
    queryKey: ['specialties'],
    queryFn: doctorService.specialties,
  });

  return (
    <>
      <PageHero
        simple
        title="Chuyên khoa tim mạch"
        description="Các đơn vị chuyên sâu phối hợp trong chẩn đoán, điều trị, can thiệp và phục hồi tim mạch."
      />
      <section className="section section-soft">
        <div className="container">
          {specialties.isLoading ? (
            <StatePanel kind="loading" />
          ) : (
            <div className={styles.grid}>
              {specialties.data?.map((specialty, index) => {
                const Icon = specialtyIcons[index];
                return (
                  <article id={specialty.id} key={specialty.id}>
                    <span><Icon size={28} /></span>
                    <div>
                      <h2>{specialty.name}</h2>
                      <p>{specialty.description}</p>
                      <small>{specialty.doctorCount} bác sĩ đang công tác</small>
                      <Link to={`/bac-si?specialty=${specialty.id}`}>
                        Xem bác sĩ <ArrowRight size={16} />
                      </Link>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
