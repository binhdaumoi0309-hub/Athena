import { FormEvent, useRef, useState } from 'react';
import { Bot, LoaderCircle, MessageCircle, RefreshCw, Send, X } from 'lucide-react';
import type { AssistantMessage } from '../../../types';
import { assistantService } from '../../../services';
import { StructuredMessage } from '../messages/StructuredMessage';
import styles from './AssistantWidget.module.css';

const welcome: AssistantMessage = { id:'welcome', role:'assistant', intent:'general', answer:'Xin chào! Tôi có thể giúp bạn tìm bác sĩ, lịch khám, bảng giá và hướng dẫn BHYT.', actions:[], structured_data:{}, emergency:false, citations:[] };
export function AssistantWidget() {
  const [open,setOpen]=useState(false); const [messages,setMessages]=useState<AssistantMessage[]>([welcome]); const [input,setInput]=useState(''); const [loading,setLoading]=useState(false); const [failed,setFailed]=useState(''); const inputRef=useRef<HTMLInputElement>(null);
  const send=async(event?:FormEvent)=>{event?.preventDefault();const value=(failed||input).trim();if(!value||loading)return;setFailed('');setInput('');setMessages((items)=>[...items,{id:crypto.randomUUID(),role:'user',intent:'general',answer:value,actions:[],structured_data:{},emergency:false,citations:[]}]);setLoading(true);try{const answer=await assistantService.send(value);setMessages((items)=>[...items,answer]);}catch{setFailed(value);}finally{setLoading(false);inputRef.current?.focus();}};
  return <div className={styles.root}>{open&&<section className={styles.panel} aria-label="Trợ lý AI">
    <header><div><Bot size={22}/><span><strong>Trợ lý Tim Hà Nội</strong><small>Thông tin tham khảo, không thay thế chẩn đoán</small></span></div><button onClick={()=>setOpen(false)} aria-label="Đóng trợ lý"><X size={20}/></button></header>
    <div className={styles.messages} aria-live="polite">{messages.map((message)=><div key={message.id} className={message.role==='user'?styles.user:styles.assistant}>{message.role==='assistant'&&<Bot size={17}/>}<div>{message.role==='assistant'?<StructuredMessage message={message}/>:<p>{message.answer}</p>}</div></div>)}{loading&&<div className={styles.loading}><LoaderCircle size={18}/>Đang tìm thông tin...</div>}{failed&&<button className={styles.retry} onClick={()=>void send()}><RefreshCw size={16}/>Không thể kết nối. Thử lại</button>}</div>
    <div className={styles.suggestions}>{['Tìm bác sĩ','Lịch khám gần nhất','Chuyên khoa phù hợp'].map((text)=><button key={text} onClick={()=>setInput(text)}>{text}</button>)}</div>
    <form onSubmit={(event)=>void send(event)}><label className="sr-only" htmlFor="assistant-input">Nhập câu hỏi</label><input ref={inputRef} id="assistant-input" value={input} onChange={(event)=>setInput(event.target.value)} placeholder="Bạn cần hỗ trợ gì?"/><button type="submit" disabled={!input.trim()||loading} aria-label="Gửi tin nhắn"><Send size={18}/></button></form>
  </section>}<button className={styles.fab} onClick={()=>setOpen((value)=>!value)} aria-label={open?'Đóng trợ lý AI':'Mở trợ lý AI'}>{open?<X/>:<MessageCircle/>}</button></div>;
}
