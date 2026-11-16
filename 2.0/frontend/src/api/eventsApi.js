/**
 * Events API — recent system events for the dashboard timeline.
 * Backend endpoint (conceptual): GET /system/events
 * Member 2: update the endpoint path/params inside fetchEvents() once finalised.
 */
import { apiClient } from './client';

/**
 * Fetch recent system events.
 * @param {{ limit?: number, severity?: string }} options
 * @returns {Promise<SystemEvent[]>}
 */
export async function fetchEvents({ limit = 50, severity } = {}) {
  const params = { limit };
  if (severity) params.severity = severity;
  const { data } = await apiClient.get('/system/events', { params });
  const list = Array.isArray(data) ? data : data.events ?? data.items ?? [];
  return list.map(normaliseEvent);
}

// ─── Normaliser ──────────────────────────────────────────────────────────────
function normaliseEvent(raw) {
  const timestamp = raw.timestamp ?? raw.time ?? raw.created_at ?? '';
  const source = raw.source ?? raw.service ?? raw.unit ?? '';
  return {
    id:          raw.id          ?? raw._id       ?? `${timestamp}:${source}`,
    timestamp,
    title:       raw.title       ?? raw.message    ?? raw.description ?? '',
    severity:    raw.severity    ?? raw.level      ?? 'unknown',
    source,
    description: raw.description ?? raw.detail     ?? null,
  };
}
