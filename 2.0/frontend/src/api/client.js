/**
 * API Client — central Axios instance + mock toggle.
 * Components must NEVER import axios directly.
 */
import axios from 'axios';

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/** Real Axios instance (used when mock is off) */
export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor — normalise error shape
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'Unknown error';
    return Promise.reject({ message, status: err.response?.status ?? 0 });
  }
);

export const isMockMode = () => USE_MOCK;
