/**
 * useNetwork — dedicated hook for network data.
 * Uses networkApi.js — never calls the API layer directly.
 *
 * Replaces the heavier useSystemStats() call in Network.jsx so that:
 *  - only network data is fetched when viewing the Network page
 *  - when the real backend has separate /system/network, this hook is the
 *    only file that needs updating (not the component)
 */
import { useState, useEffect, useCallback } from 'react';
import { fetchNetwork } from '../api/networkApi';

/**
 * @param {number} [autoRefreshMs=0]  Set > 0 to poll on an interval.
 */
export function useNetwork(autoRefreshMs = 1000) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const network = await fetchNetwork();
      setData(network);
    } catch (err) {
      setError(err?.message ?? 'Failed to load network data.');
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
