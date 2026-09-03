import { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchProcesses } from '../api/processApi';

export function useProcesses(autoRefreshMs = 1000) {
  const [processes, setProcesses] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [sortKey, setSortKey]     = useState('cpu_percent');
  const [sortDir, setSortDir]     = useState('desc');

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchProcesses();
      setProcesses(data);
    } catch (err) {
      setError(err?.message ?? 'Failed to load processes.');
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

  // Memoised sort — only re-runs when processes, sortKey, or sortDir changes
  const sorted = useMemo(() => {
    return [...processes].sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      return sortDir === 'desc' ? bv - av : av - bv;
    });
  }, [processes, sortKey, sortDir]);

  const toggleSort = useCallback((key) => {
    if (sortKey === key) setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    else { setSortKey(key); setSortDir('desc'); }
  }, [sortKey]);

  return { processes: sorted, loading, error, reload: load, sortKey, sortDir, toggleSort };
}
