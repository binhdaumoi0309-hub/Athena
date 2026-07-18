import type { AvailableDoctor, Facility, ScheduleDay } from '../types';
import { bookingApiClient } from './bookingApiClient';

function queryString(values: Record<string, string | undefined>): string {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `?${query}` : '';
}

export const scheduleService = {
  facilities: async (): Promise<Facility[]> => bookingApiClient.get('/facilities'),

  doctors: async (facilityId: string): Promise<AvailableDoctor[]> =>
    bookingApiClient.get(
      `/booking/doctors${queryString({ facility_id: facilityId })}`,
    ),

  list: async (doctor?: string, facilityId?: string): Promise<ScheduleDay[]> =>
    bookingApiClient.get(
      `/schedules${queryString({ doctor, facility: facilityId })}`,
    ),
};
