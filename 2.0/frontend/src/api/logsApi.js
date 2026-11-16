import { apiClient } from './client';

export async function fetchLogs({ severity, service, search, limit = 200 } = {}) {
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
    service:   raw.service   ?? raw.unit      ?? null,
    message:   raw.message   ?? raw.msg       ?? '',
    severity:  raw.severity  ?? raw.level     ?? 'unknown',
    pid:       raw.pid       ?? null,
  };
}
