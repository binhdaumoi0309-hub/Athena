import { AlertTriangle, CalendarDays, CheckCircle2, ExternalLink, Stethoscope, WalletCards } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { AssistantMessage } from '../../../types';
import styles from './StructuredMessage.module.css';

export function StructuredMessage({ message }: { message: AssistantMessage }) {
  return <div className={styles.content}>
    {message.emergency && <div className={styles.emergency} role="alert"><AlertTriangle size={20}/><div><strong>Cảnh báo cấp cứu</strong><span>Không chờ phản hồi trực tuyến nếu triệu chứng đang diễn tiến.</span></div></div>}
    <p>{message.answer}</p>
    {message.structured_data.doctors?.map((doctor) => <article className={styles.card} key={doctor.id}><img src={doctor.image} alt=""/><div><strong>{doctor.title} {doctor.name}</strong><span><Stethoscope size={13}/>{doctor.specialty}</span><Link to={`/bac-si/${doctor.id}`}>Xem bác sĩ</Link></div></article>)}
    {message.structured_data.schedules?.map((day) => <article className={styles.schedule} key={day.date}><CalendarDays size={18}/><div><strong>{day.label}</strong><span>{day.slots.filter((slot)=>slot.status==='available').slice(0,4).map((slot)=>slot.time).join(' · ')}</span></div></article>)}
    {message.structured_data.prices?.map((item) => <article className={styles.price} key={item.id}><WalletCards size={17}/><span>{item.service}</span><strong>{item.price.toLocaleString('vi-VN')}đ</strong></article>)}
    {message.structured_data.checklist && <ul className={styles.checklist}>{message.structured_data.checklist.map((item) => <li key={item}><CheckCircle2 size={16}/>{item}</li>)}</ul>}
    {message.actions.length>0&&<div className={styles.actions}>{message.actions.map((action)=>action.href?.startsWith('/')?<Link key={action.id} to={action.href}>{action.label}</Link>:<a key={action.id} href={action.href}>{action.label}</a>)}</div>}
    {message.citations.length>0&&<div className={styles.citations}>{message.citations.map((citation)=><a key={citation.url} href={citation.url}><ExternalLink size={12}/>{citation.title}</a>)}</div>}
  </div>;
}
