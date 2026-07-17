import { apiClient, mockDelay } from './apiClient';

export interface AuthCredentials { phone: string; password: string; }
export interface RegisterPayload extends AuthCredentials { fullName: string; email: string; }
export interface AuthUser { id: string; fullName: string; phone: string; email: string; }

const mockUser: AuthUser = { id: 'patient-1', fullName: 'Nguyễn Minh Anh', phone: '0912345678', email: 'minhanh@example.com' };
export const authService = {
  login: async (payload: AuthCredentials): Promise<AuthUser> => apiClient.useMocks ? mockDelay({ ...mockUser, phone: payload.phone }) : apiClient.post('/auth/login', payload),
  register: async (payload: RegisterPayload): Promise<AuthUser> => apiClient.useMocks ? mockDelay({ ...mockUser, fullName: payload.fullName, phone: payload.phone, email: payload.email }) : apiClient.post('/auth/register', payload),
  forgotPassword: async (phone: string): Promise<void> => apiClient.useMocks ? mockDelay(undefined) : apiClient.post('/auth/forgot-password', { phone }),
};
