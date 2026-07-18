import { specialties } from '../mocks/data';
import type { Doctor, Specialty } from '../types';
import { mockDelay } from './apiClient';
import { bookingApiClient } from './bookingApiClient';

interface DoctorCatalogResponse {
  id: string;
  title: string;
  content: string;
  zone: string;
  facility_id: string;
  image: string;
}

function mapDoctor(item: DoctorCatalogResponse): Doctor {
  return {
    id: item.id,
    name: item.title,
    title: '',
    specialtyId: '',
    specialty: '',
    experience: 0,
    rating: 0,
    reviews: 0,
    facilityId: item.facility_id,
    image: item.image || '/images/doctor-placeholder.svg',
    languages: [],
    education: [],
    about: item.content,
  };
}

export const doctorService = {
  list: async (): Promise<Doctor[]> => {
    const response = await bookingApiClient.get<DoctorCatalogResponse[]>('/doctors');
    return response.map(mapDoctor);
  },
  getById: async (id: string): Promise<Doctor | null> => {
    const response = await bookingApiClient.get<DoctorCatalogResponse>(`/doctors/${encodeURIComponent(id)}`);
    return mapDoctor(response);
  },
  specialties: async (): Promise<Specialty[]> => mockDelay(specialties),
};
