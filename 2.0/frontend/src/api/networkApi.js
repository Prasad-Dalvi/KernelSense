import { apiClient } from './client';

export async function fetchNetwork() {
  const { data } = await apiClient.get('/system/network');
  return normaliseNetwork(data);
}

function normaliseNetwork(raw) {
  if (Array.isArray(raw)) {
    return { interfaces: raw.map(normaliseIface), internet: null, download_mbps: null, upload_mbps: null };
  }
  return {
    interfaces:    (raw?.interfaces ?? []).map(normaliseIface),
    internet:       raw?.internet ?? raw?.internet_available ?? null,
    download_mbps:  raw?.download_mbps ?? null,
    upload_mbps:    raw?.upload_mbps   ?? null,
  };
}

function normaliseIface(i) {
  return {
    name:   i?.name       ?? i?.interface ?? null,
    status: i?.status     ?? (typeof i?.is_up === 'boolean' ? (i.is_up ? 'up' : 'down') : null),
    ip:     i?.ip_address ?? i?.ip ?? null,
    type:   i?.type       ?? null,
  };
}
