import { doctors, specialties } from '../mocks/data';
import type { Doctor, Specialty } from '../types';
import { apiClient, mockDelay } from './apiClient';

export const doctorService = {
  list: async (specialtyId?: string): Promise<Doctor[]> => {
    if (!apiClient.useMocks) return apiClient.get(`/doctors${specialtyId ? `?specialty=${specialtyId}` : ''}`);
    return mockDelay(specialtyId ? doctors.filter((doctor) => doctor.specialtyId === specialtyId) : doctors);
  },
  getById: async (id: string): Promise<Doctor | null> => apiClient.useMocks ? mockDelay(doctors.find((doctor) => doctor.id === id) ?? null) : apiClient.get(`/doctors/${id}`),
  specialties: async (): Promise<Specialty[]> => apiClient.useMocks ? mockDelay(specialties) : apiClient.get('/specialties'),
};
