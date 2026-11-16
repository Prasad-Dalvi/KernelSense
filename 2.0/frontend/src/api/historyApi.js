import { apiClient } from './client';

export async function fetchHistory() {
  const { data } = await apiClient.get('/history');
  const list = Array.isArray(data) ? data : data.items ?? [];
  return list.map(normaliseHistoryItem);
}

function normaliseHistoryItem(raw) {
  return {
    id:         raw.id          ?? Math.random().toString(36).slice(2),
    query:      raw.query       ?? raw.user_query ?? '',
    timestamp:  raw.timestamp   ?? raw.created_at ?? '',
    intent:     raw.intent      ?? null,
    commands:   raw.commands    ?? [],
    result:     raw.result      ?? raw.response ?? '',
    risk_level: raw.risk_level  ?? null,
    status:     raw.status      ?? null,
  };
}
