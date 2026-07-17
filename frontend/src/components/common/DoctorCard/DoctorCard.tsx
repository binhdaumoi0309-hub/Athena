import { CalendarDays, MapPin, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Doctor } from '../../../types';
import styles from './DoctorCard.module.css';
export function DoctorCard({ doctor }: { doctor: Doctor }) { return <article className={styles.card}><img src={doctor.image} alt={`${doctor.title} ${doctor.name}`} width="320" height="360" loading="lazy"/><div className={styles.content}><div className={styles.rating}><Star size={15} fill="currentColor"/>{doctor.rating}<span>({doctor.reviews} đánh giá)</span></div><h2>{doctor.title} {doctor.name}</h2><p className={styles.specialty}>{doctor.specialty}</p><p><MapPin size={15}/> {doctor.facilityId==='cs1'?'Cơ sở 1':'Cơ sở 2'} · {doctor.experience} năm kinh nghiệm</p><div className={styles.actions}><Link to={`/bac-si/${doctor.id}`}>Xem hồ sơ</Link><Link to={`/dat-lich?doctor=${doctor.id}`}><CalendarDays size={16}/>Đặt lịch</Link></div></div></article>; }
