import { facilities, schedules } from '../mocks/data';
import type { Facility, ScheduleDay } from '../types';
import { apiClient, mockDelay } from './apiClient';

export const scheduleService = {
  facilities: async (): Promise<Facility[]> => apiClient.useMocks ? mockDelay(facilities) : apiClient.get('/facilities'),
  list: async (doctorId?: string): Promise<ScheduleDay[]> => apiClient.useMocks ? mockDelay(schedules) : apiClient.get(`/schedules${doctorId ? `?doctor=${doctorId}` : ''}`),
};
