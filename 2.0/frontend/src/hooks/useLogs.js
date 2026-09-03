import { useState, useEffect, useCallback } from 'react';
import { fetchLogs } from '../api/logsApi';

export function useLogs(autoRefreshMs = 0) {
  const [logs, setLogs]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [filters, setFilters]   = useState({ severity: '', service: '', search: '' });

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchLogs(filters);
      setLogs(data);
    } catch (err) {
      setError(err?.message ?? 'Failed to load logs.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
    if (autoRefreshMs > 0) {
      const id = setInterval(load, autoRefreshMs);
      return () => clearInterval(id);
    }
  }, [load, autoRefreshMs]);

  const updateFilter = (key, value) => setFilters((f) => ({ ...f, [key]: value }));

  return { logs, loading, error, filters, updateFilter, reload: load };
}
