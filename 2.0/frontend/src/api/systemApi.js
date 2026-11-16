import { apiClient } from './client';

export async function fetchSystemStats() {
  try {
    const { data } = await apiClient.get('/system/stats');
    if (data && data.cpu && data.memory) {
      return normaliseSystemStats(data);
    }
  } catch {
    // Fall back to parallel individual endpoints if /system/stats is unavailable
  }
  const [cpu, memory, storage, network, health] = await Promise.all([
    apiClient.get('/system/cpu'),
    apiClient.get('/system/memory'),
    apiClient.get('/system/storage'),
    apiClient.get('/system/network'),
    apiClient.get('/system/health'),
  ]);
  return normaliseSystemStats({
    cpu: cpu.data, memory: memory.data, storage: storage.data,
    network: network.data, health: health.data,
  });
}

export async function fetchCpu()     { const { data } = await apiClient.get('/system/cpu');     return normaliseCpu(data); }
export async function fetchMemory()  { const { data } = await apiClient.get('/system/memory');  return normaliseMemory(data); }
export async function fetchStorage() { const { data } = await apiClient.get('/system/storage'); return normaliseStorage(data); }
export async function fetchNetwork() { const { data } = await apiClient.get('/system/network'); return normaliseNetwork(data); }
export async function fetchHealth()  { const { data } = await apiClient.get('/system/health');  return normaliseHealth(data); }
export async function fetchHostInfo() { const { data } = await apiClient.get('/system/info'); return data; }

// ─── Normalisers ─────────────────────────────────────────────────────────────
function normaliseSystemStats(raw) {
  return {
    cpu:     normaliseCpu(raw.cpu),
    memory:  normaliseMemory(raw.memory),
    storage: normaliseStorage(raw.storage),
    network: normaliseNetwork(raw.network),
    health:  normaliseHealth(raw.health),
  };
}

function normaliseHistory(rawHistory) {
  if (Array.isArray(rawHistory) && rawHistory.length > 0) {
    return rawHistory.flatMap((item, idx) => {
      if (typeof item === 'number' && Number.isFinite(item)) {
        return [{ time: `${idx}`, value: item }];
      }
      if (typeof item === 'object' && item !== null) {
        const val = item.value ?? item.usage ?? item.val;
        if (typeof val === 'number' && Number.isFinite(val)) {
          return [{ time: item.time ?? `${idx}`, value: val }];
        }
      }
      return [];
    });
  }
  return [];
}

function normaliseCpu(raw) {
  const usage = raw?.cpu_usage ?? raw?.usage ?? null;
  return {
    usage,
    cores:       raw?.cpu_count       ?? raw?.cores       ?? null,
    load_avg:    raw?.load_avg        ?? null,
    temperature: raw?.temperature     ?? null,
    history:     normaliseHistory(raw?.history),
  };
}

function normaliseMemory(raw) {
  const usage = raw?.memory_percent ?? raw?.usage ?? null;
  return {
    usage,
    total_gb:      raw?.total_gb      ?? raw?.total      ?? null,
    used_gb:       raw?.used_gb       ?? raw?.used       ?? null,
    free_gb:       raw?.free_gb       ?? raw?.free       ?? null,
    swap_used:     raw?.swap_used_gb  ?? null,
    swap_total:    raw?.swap_total_gb ?? null,
    swap_percent:  raw?.swap_percent  ?? null,
    history:       normaliseHistory(raw?.history),
  };
}

function normaliseStorage(raw) {
  return {
    usage:           raw?.usage_percent ?? raw?.usage         ?? null,
    total_gb:        raw?.total         ?? raw?.total_gb      ?? null,
    used_gb:         raw?.used          ?? raw?.used_gb       ?? null,
    available_gb:    raw?.available     ?? raw?.available_gb  ?? null,
    partitions:      raw?.partitions    ?? [],
    recommendations: raw?.recommendations ?? [],
  };
}

function normaliseNetwork(raw) {
  if (Array.isArray(raw)) return { interfaces: raw.map(normaliseInterface), internet: null };
  return {
    interfaces: (raw?.interfaces ?? []).map(normaliseInterface),
    internet:   raw?.internet ?? raw?.internet_available ?? null,
    download_mbps: raw?.download_mbps ?? null,
    upload_mbps:   raw?.upload_mbps   ?? null,
  };
}

function normaliseInterface(iface) {
  return {
    name:    iface?.name       ?? iface?.interface ?? null,
    status:  iface?.status     ?? (typeof iface?.is_up === 'boolean' ? (iface.is_up ? 'up' : 'down') : null),
    ip:      iface?.ip_address ?? iface?.ip ?? null,
    type:    iface?.type       ?? null,
  };
}

function normaliseHealth(raw) {
  return {
    score:       raw?.score ?? raw?.overall_score ?? null,
    categories:  (raw?.categories ?? []).map((c) => ({
      name:           c.name            ?? '',
      score:          c.score           ?? null,
      status:         c.status          ?? 'unknown',
      explanation:    c.explanation     ?? c.reason ?? '',
      recommendation: c.recommendation  ?? '',
    })),
  };
}
