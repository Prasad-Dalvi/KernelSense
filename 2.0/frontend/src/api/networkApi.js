import { apiClient, isMockMode } from './client';
import { getMockNetwork } from '../mock/mockNetwork';

export async function fetchNetwork() {
  if (isMockMode()) return getMockNetwork();
  const { data } = await apiClient.get('/system/network');
  return normaliseNetwork(data);
}

function normaliseNetwork(raw) {
  if (Array.isArray(raw)) {
    return { interfaces: raw.map(normaliseIface), internet: true, download_mbps: null, upload_mbps: null };
  }
  return {
    interfaces:    (raw?.interfaces ?? []).map(normaliseIface),
    internet:       raw?.internet ?? raw?.internet_available ?? false,
    download_mbps:  raw?.download_mbps ?? null,
    upload_mbps:    raw?.upload_mbps   ?? null,
  };
}

function normaliseIface(i) {
  return {
    name:   i?.name       ?? i?.interface ?? 'unknown',
    status: i?.status     ?? (i?.is_up ? 'up' : 'down'),
    ip:     i?.ip_address ?? i?.ip ?? null,
    type:   i?.type       ?? 'ethernet',
  };
}
