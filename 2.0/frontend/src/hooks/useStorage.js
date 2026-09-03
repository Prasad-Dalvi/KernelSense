/**
 * useStorage — dedicated hook for storage data.
 * Uses storageApi.js — never calls the API layer directly.
 *
 * Replaces the heavier useSystemStats() call in Storage.jsx so that:
 *  - only storage data is fetched when viewing the Storage page
 *  - when the real backend has a separate /system/storage, this hook is the
 *    only file that needs updating (not the component)
 */
import { useState, useEffect, useCallback } from 'react';
import { fetchStorage } from '../api/storageApi';

/**
 * @param {number} [autoRefreshMs=0]  Set > 0 to poll on an interval.
 */
export function useStorage(autoRefreshMs = 2000) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const storage = await fetchStorage();
      setData(storage);
    } catch (err) {
      setError(err?.message ?? 'Failed to load storage data.');
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
