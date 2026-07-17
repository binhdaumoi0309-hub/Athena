import type { BookingData, Doctor, Facility, ScheduleDay, Specialty } from '../../types';
export interface BookingStepProps { data: BookingData; update: (values: Partial<BookingData>) => void; facilities: Facility[]; specialties: Specialty[]; doctors: Doctor[]; schedules: ScheduleDay[]; }
