import { apiClient, isMockMode } from './client';
import { getMockSystem } from '../mock/mockSystem';

export async function fetchSystemStats() {
  if (isMockMode()) return getMockSystem();
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

export async function fetchCpu()     { if (isMockMode()) return getMockSystem().cpu;     const { data } = await apiClient.get('/system/cpu');     return normaliseCpu(data); }
export async function fetchMemory()  { if (isMockMode()) return getMockSystem().memory;  const { data } = await apiClient.get('/system/memory');  return normaliseMemory(data); }
export async function fetchStorage() { if (isMockMode()) return getMockSystem().storage; const { data } = await apiClient.get('/system/storage'); return normaliseStorage(data); }
export async function fetchNetwork() { if (isMockMode()) return getMockSystem().network; const { data } = await apiClient.get('/system/network'); return normaliseNetwork(data); }
export async function fetchHealth()  { if (isMockMode()) return getMockSystem().health;  const { data } = await apiClient.get('/system/health');  return normaliseHealth(data); }

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

function normaliseHistory(rawHistory, currentVal = 0) {
  if (Array.isArray(rawHistory) && rawHistory.length > 0) {
    return rawHistory.map((item, idx) => {
      if (typeof item === 'number') {
        return { time: `${idx}`, value: Number(item) || 0 };
      }
      if (typeof item === 'object' && item !== null) {
        const val = typeof item.value === 'number' ? item.value : (Number(item.usage) || Number(item.val) || currentVal);
        return { time: item.time ?? `${idx}`, value: val };
      }
      return { time: `${idx}`, value: currentVal };
    });
  }
  return Array.from({ length: 15 }, (_, i) => ({
    time: `${i}`,
    value: currentVal,
  }));
}

function normaliseCpu(raw) {
  const usage = raw?.cpu_usage ?? raw?.usage ?? 0;
  return {
    usage,
    cores:       raw?.cpu_count       ?? raw?.cores       ?? 0,
    load_avg:    raw?.load_avg        ?? [],
    temperature: raw?.temperature     ?? null,
    history:     normaliseHistory(raw?.history, usage),
  };
}

function normaliseMemory(raw) {
  const usage = raw?.memory_percent ?? raw?.usage ?? 0;
  return {
    usage,
    total_gb:  raw?.total_gb      ?? raw?.total      ?? 0,
    used_gb:   raw?.used_gb       ?? raw?.used       ?? 0,
    free_gb:   raw?.free_gb       ?? raw?.free       ?? 0,
    swap_used: raw?.swap_percent  ?? raw?.swap_used  ?? 0,
    history:   normaliseHistory(raw?.history, usage),
  };
}

function normaliseStorage(raw) {
  return {
    usage:         raw?.usage_percent ?? raw?.usage         ?? 0,
    total_gb:      raw?.total         ?? raw?.total_gb      ?? 0,
    used_gb:       raw?.used          ?? raw?.used_gb       ?? 0,
    available_gb:  raw?.available     ?? raw?.available_gb  ?? 0,
    largest_dirs:  raw?.largest_dirs  ?? [],
    large_files:   raw?.large_files   ?? [],
    recommendations: raw?.recommendations ?? [],
  };
}

function normaliseNetwork(raw) {
  if (Array.isArray(raw)) return { interfaces: raw.map(normaliseInterface), internet: true };
  return {
    interfaces: (raw?.interfaces ?? []).map(normaliseInterface),
    internet:   raw?.internet ?? raw?.internet_available ?? false,
    download_mbps: raw?.download_mbps ?? null,
    upload_mbps:   raw?.upload_mbps   ?? null,
  };
}

function normaliseInterface(iface) {
  return {
    name:    iface?.name       ?? iface?.interface ?? 'unknown',
    status:  iface?.status     ?? (iface?.is_up ? 'up' : 'down'),
    ip:      iface?.ip_address ?? iface?.ip ?? null,
    type:    iface?.type       ?? 'ethernet',
  };
}

function normaliseHealth(raw) {
  return {
    score:       raw?.score ?? raw?.overall_score ?? 0,
    categories:  (raw?.categories ?? []).map((c) => ({
      name:           c.name            ?? '',
      score:          c.score           ?? 0,
      status:         c.status          ?? 'unknown',
      explanation:    c.explanation     ?? c.reason ?? '',
      recommendation: c.recommendation  ?? '',
    })),
  };
}
