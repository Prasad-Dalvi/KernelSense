import { useState, useEffect, useCallback } from 'react';
import { fetchHostInfo } from '../api/systemApi';

export function useHostInfo(autoRefreshMs = 30000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const hostInfo = await fetchHostInfo();
      setData(hostInfo);
      setError(null);
    } catch (err) {
      setData(null);
      setError(err?.message ?? 'Failed to load host information.');
    }
  }, []);

  useEffect(() => {
    load();
    if (autoRefreshMs > 0) {
      const id = setInterval(load, autoRefreshMs);
      return () => clearInterval(id);
    }
  }, [load, autoRefreshMs]);

  return { data, error, reload: load };
}
