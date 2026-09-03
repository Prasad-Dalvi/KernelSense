import { apiClient, isMockMode } from './client';
import { getMockStorage } from '../mock/mockStorage';

export async function fetchStorage() {
  if (isMockMode()) return getMockStorage();
  const { data } = await apiClient.get('/system/storage');
  return normaliseStorage(data);
}

function normaliseStorage(raw) {
  return {
    usage:           raw?.usage_percent ?? raw?.usage        ?? 0,
    total_gb:        raw?.total         ?? raw?.total_gb     ?? 0,
    used_gb:         raw?.used          ?? raw?.used_gb      ?? 0,
    available_gb:    raw?.available     ?? raw?.available_gb ?? 0,
    largest_dirs:    raw?.largest_dirs  ?? [],
    large_files:     raw?.large_files   ?? [],
    recommendations: raw?.recommendations ?? [],
    history:         raw?.history       ?? [],
  };
}
