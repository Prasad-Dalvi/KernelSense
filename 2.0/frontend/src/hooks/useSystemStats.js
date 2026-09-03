import { useState, useEffect, useCallback } from 'react';
import { fetchSystemStats } from '../api/systemApi';

export function useSystemStats(autoRefreshMs = 1000) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const stats = await fetchSystemStats();
      setData(stats);
    } catch (err) {
      setError(err?.message ?? 'Failed to load system stats.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    if (autoRefreshMs > 0) {
      const id = setInterval(load, autoRefreshMs);
      return () => clearInterval(id);
    }
  }, [load, autoRefreshMs]);

  return { data, loading, error, reload: load };
}
