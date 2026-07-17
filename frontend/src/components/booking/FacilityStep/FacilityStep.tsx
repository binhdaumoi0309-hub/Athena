import { Building2, CheckCircle2, Clock3, MapPin } from 'lucide-react';
import type { BookingStepProps } from '../types';
import styles from './FacilityStep.module.css';
export function FacilityStep({data,update,facilities}:BookingStepProps){return <div className={styles.grid}>{facilities.map((facility)=><button type="button" key={facility.id} className={data.facilityId===facility.id?styles.selected:undefined} onClick={()=>update({facilityId:facility.id,doctorId:''})}><img src={facility.image} alt=""/><span><strong>{facility.name}</strong><small><MapPin/> {facility.address}</small><small><Clock3/> {facility.hours}</small></span>{data.facilityId===facility.id?<CheckCircle2 className={styles.check}/>:<Building2 className={styles.building}/>}</button>)}</div>}
