import { apiClient, isMockMode } from './client';
import { getMockProcesses } from '../mock/mockProcesses';

export async function fetchProcesses() {
  if (isMockMode()) return getMockProcesses();
  const { data } = await apiClient.get('/processes');
  const list = Array.isArray(data) ? data : data.processes ?? [];
  return list.map(normaliseProcess);
}

export async function killProcess(pid) {
  if (isMockMode()) return { success: true };
  const { data } = await apiClient.post(`/processes/${pid}/kill`);
  return data;
}

function normaliseProcess(raw) {
  return {
    pid:            raw.pid            ?? 0,
    name:           raw.name           ?? '',
    cpu_percent:    raw.cpu_percent    ?? raw.cpu  ?? 0,
    memory_percent: raw.memory_percent ?? raw.mem  ?? 0,
    user:           raw.user           ?? raw.username ?? '',
    status:         raw.status         ?? 'running',
    memory_mb:      raw.memory_mb      ?? null,
  };
}
