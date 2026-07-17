import { prices } from '../mocks/data';
import type { PriceItem } from '../types';
import { apiClient, mockDelay } from './apiClient';

export const pricingService = {
  list: async (): Promise<PriceItem[]> => apiClient.useMocks ? mockDelay(prices) : apiClient.get('/pricing'),
};
