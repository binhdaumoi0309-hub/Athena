import { Mic, Square } from 'lucide-react';
import styles from './VoiceInputOverlay.module.css';

interface VoiceInputOverlayProps {
  transcript: string;
  onStop: () => void;
}

export function VoiceInputOverlay({ transcript, onStop }: VoiceInputOverlayProps) {
  return (
    <div className={styles.backdrop} role="dialog" aria-modal="true" aria-label="Nhập nội dung bằng giọng nói">
      <div className={styles.dialog}>
        <button className={styles.micButton} type="button" onClick={onStop} aria-label="Dừng ghi âm và gửi">
          <Mic size={48} strokeWidth={1.8} />
          <span className={styles.pulse} />
        </button>

        <div className={styles.wave} aria-hidden="true">
          <span /><span /><span /><span /><span />
        </div>

        <p className={styles.status}>Đang nghe...</p>
        <div className={styles.transcript} aria-live="polite">
          {transcript || 'Hãy bắt đầu nói nội dung bạn muốn gửi'}
        </div>
        <button className={styles.stopButton} type="button" onClick={onStop}>
          <Square size={15} fill="currentColor" /> Dừng và gửi
        </button>
        <small>Tin nhắn sẽ tự gửi khi bạn ngừng nói trong vài giây</small>
      </div>
    </div>
  );
}
