/**
 * Events API — recent system events for the dashboard timeline.
 * Backend endpoint (conceptual): GET /system/events
 * Member 2: update the endpoint path/params inside fetchEvents() once finalised.
 */
import { apiClient, isMockMode } from './client';
import { getMockRecentEvents } from '../mock/mockSystem';

/**
 * Fetch recent system events.
 * @param {{ limit?: number, severity?: string }} options
 * @returns {Promise<SystemEvent[]>}
 */
export async function fetchEvents({ limit = 50, severity } = {}) {
  if (isMockMode()) {
    let events = getMockRecentEvents();
    if (severity) events = events.filter((e) => e.severity === severity);
    return events.slice(0, limit);
  }
  const params = { limit };
  if (severity) params.severity = severity;
  const { data } = await apiClient.get('/system/events', { params });
  const list = Array.isArray(data) ? data : data.events ?? data.items ?? [];
  return list.map(normaliseEvent);
}

// ─── Normaliser ──────────────────────────────────────────────────────────────
function normaliseEvent(raw) {
  return {
    id:          raw.id          ?? raw._id       ?? Math.random().toString(36).slice(2),
    timestamp:   raw.timestamp   ?? raw.time       ?? raw.created_at ?? '',
    title:       raw.title       ?? raw.message    ?? raw.description ?? '',
    severity:    raw.severity    ?? raw.level      ?? 'info',
    source:      raw.source      ?? raw.service    ?? raw.unit ?? 'system',
    description: raw.description ?? raw.detail     ?? null,
  };
}
