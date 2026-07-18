import { appointments } from '../mocks/data';
import type { Appointment, BookingData } from '../types';
import { apiClient, mockDelay } from './apiClient';
import { bookingApiClient } from './bookingApiClient';

export const appointmentService = {
  list: async (): Promise<Appointment[]> => apiClient.useMocks ? mockDelay(appointments) : bookingApiClient.get('/appointments/me'),
  create: async (data: BookingData): Promise<Appointment> => {
    if (!apiClient.useMocks) return bookingApiClient.post('/appointments', data);
    const result: Appointment = { id: crypto.randomUUID(), code: `BVT-${Date.now().toString().slice(-8)}`, doctorName: data.doctorId || 'Bác sĩ theo phân công', specialty: data.specialtyId, facilityName: data.facilityId, date: data.date, time: data.time, status: 'upcoming', patientName: data.patientName };
    return mockDelay(result, 600);
  },
};
