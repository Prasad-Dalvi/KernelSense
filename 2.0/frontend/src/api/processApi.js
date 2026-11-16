import { apiClient } from './client';

export async function fetchProcesses() {
  const { data } = await apiClient.get('/processes', { params: { limit: 500 } });
  const list = Array.isArray(data) ? data : data.processes ?? [];
  return list.map(normaliseProcess);
}

export async function killProcess(pid) {
  const { data } = await apiClient.post(`/processes/${pid}/kill`);
  return data;
}

function normaliseProcess(raw) {
  return {
    pid:            raw.pid            ?? null,
    name:           raw.name           ?? null,
    cpu_percent:    raw.cpu_percent    ?? raw.cpu  ?? null,
    memory_percent: raw.memory_percent ?? raw.mem  ?? null,
    user:           raw.user           ?? raw.username ?? null,
    status:         raw.status         ?? null,
    memory_mb:      raw.memory_mb      ?? null,
  };
}
