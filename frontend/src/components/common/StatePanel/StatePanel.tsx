import { AlertTriangle, Inbox, LoaderCircle, RefreshCw, WifiOff } from 'lucide-react';
import styles from './StatePanel.module.css';
type Kind = 'loading'|'empty'|'error'|'offline'|'emergency';
interface Props { kind: Kind; title?: string; description?: string; onRetry?: () => void; }
const icons = { loading: LoaderCircle, empty: Inbox, error: AlertTriangle, offline: WifiOff, emergency: AlertTriangle };
export function StatePanel({ kind, title, description, onRetry }: Props) { const Icon=icons[kind]; return <div className={`${styles.panel} ${styles[kind]}`} role={kind === 'error'||kind === 'emergency' ? 'alert' : 'status'}><Icon className={kind==='loading'?styles.spin:undefined} size={34}/><h2>{title ?? (kind==='loading'?'Đang tải dữ liệu':kind==='empty'?'Chưa có dữ liệu':'Đã xảy ra lỗi')}</h2>{description&&<p>{description}</p>}{onRetry&&<button onClick={onRetry}><RefreshCw size={17}/>Thử lại</button>}</div>; }
