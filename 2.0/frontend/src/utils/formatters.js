/**
 * Formatting utilities for KernelSense.
 * Use these throughout the UI — never format values inline inside components.
 */

/**
 * Format a byte count as a human-readable string.
 * @param {number} bytes
 * @param {number} [decimals=1]
 * @returns {string}  e.g. "4.2 GB"
 */
export function formatBytes(bytes, decimals = 1) {
  if (bytes == null || isNaN(bytes)) return '—';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k));
  return `${(bytes / k ** i).toFixed(decimals)} ${units[i]}`;
}

/**
 * Format a gigabyte value (already in GB).
 * @param {number} gb
 * @param {number} [decimals=1]
 * @returns {string}  e.g. "10.7 GB"
 */
export function formatGB(gb, decimals = 1) {
  if (gb == null || isNaN(gb)) return '—';
  return `${Number(gb).toFixed(decimals)} GB`;
}

/**
 * Format a percentage value.
 * @param {number} value
 * @param {number} [decimals=1]
 * @returns {string}  e.g. "42.0%"
 */
export function formatPercent(value, decimals = 1) {
  if (value == null || isNaN(value)) return '—';
  return `${Number(value).toFixed(decimals)}%`;
}

/**
 * Format a network speed value.
 * @param {number|null} mbps
 * @returns {string}  e.g. "94.2 Mbps" or "—"
 */
export function formatMbps(mbps) {
  if (mbps == null || isNaN(mbps)) return '—';
  return `${Number(mbps).toFixed(1)} Mbps`;
}

/**
 * Format a timestamp (ISO string or epoch ms) as a locale time string.
 * @param {string|number} ts
 * @returns {string}
 */
export function formatTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return isNaN(d.getTime()) ? String(ts) : d.toLocaleTimeString();
}

/**
 * Format a timestamp as a locale date + time string.
 * @param {string|number} ts
 * @returns {string}
 */
export function formatDateTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return isNaN(d.getTime()) ? String(ts) : d.toLocaleString();
}

/**
 * Format a memory value in MB, auto-upgrading to GB if >= 1024.
 * @param {number|null} mb
 * @returns {string}  e.g. "1.2 GB" or "512 MB" or "—"
 */
export function formatMemoryMB(mb) {
  if (mb == null || isNaN(mb)) return '—';
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${Math.round(mb)} MB`;
}

/**
 * Clamp a number to [0, 100] — safe for progress/bar rendering.
 * @param {number} value
 * @returns {number}
 */
export function clampPercent(value) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}
