import { apiClient, isMockMode } from './client';
import { getMockLogs } from '../mock/mockLogs';

export async function fetchLogs({ severity, service, search, limit = 200 } = {}) {
  if (isMockMode()) {
    let logs = getMockLogs();
    if (severity) logs = logs.filter((l) => l.severity === severity);
    if (service)  logs = logs.filter((l) => l.service?.toLowerCase().includes(service.toLowerCase()));
    if (search)   logs = logs.filter((l) => l.message?.toLowerCase().includes(search.toLowerCase()));
    return logs.slice(0, limit);
  }
  const params = {};
  if (severity) params.severity = severity;
  if (service)  params.service  = service;
  if (search)   params.search   = search;
  params.limit = limit;
  const { data } = await apiClient.get('/logs', { params });
  const list = Array.isArray(data) ? data : data.logs ?? [];
  return list.map(normaliseLog);
}

function normaliseLog(raw) {
  return {
    id:        raw.id        ?? raw._id       ?? Math.random().toString(36).slice(2),
    timestamp: raw.timestamp ?? raw.time      ?? '',
    service:   raw.service   ?? raw.unit      ?? 'system',
    message:   raw.message   ?? raw.msg       ?? '',
    severity:  raw.severity  ?? raw.level     ?? 'info',
    pid:       raw.pid       ?? null,
  };
}
