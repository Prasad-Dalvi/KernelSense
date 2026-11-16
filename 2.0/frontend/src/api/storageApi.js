import { apiClient } from './client';

export async function fetchStorage() {
  const { data } = await apiClient.get('/system/storage');
  return normaliseStorage(data);
}

function normaliseStorage(raw) {
  return {
    usage:           raw?.usage_percent ?? raw?.usage        ?? null,
    total_gb:        raw?.total         ?? raw?.total_gb     ?? null,
    used_gb:         raw?.used          ?? raw?.used_gb      ?? null,
    available_gb:    raw?.available     ?? raw?.available_gb ?? null,
    partitions:      raw?.partitions    ?? [],
    recommendations: raw?.recommendations ?? [],
    history:         raw?.history       ?? [],
  };
}
