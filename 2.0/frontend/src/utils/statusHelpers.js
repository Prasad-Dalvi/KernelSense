/**
 * Status helpers for KernelSense.
 * Centralises threshold logic so components don't contain magic numbers.
 * If Member 2's backend sends a computed status field, prefer that — these
 * are frontend fallbacks for when the backend does not include one.
 */

/** @typedef {'good'|'warning'|'critical'|'unknown'} Status */

// ─── CPU ─────────────────────────────────────────────────────────────────────

/**
 * Derive CPU status from usage percentage.
 * @param {number} usagePercent
 * @returns {Status}
 */
export function cpuStatus(usagePercent) {
  if (usagePercent == null) return 'unknown';
  if (usagePercent > 85) return 'critical';
  if (usagePercent > 65) return 'warning';
  return 'good';
}

// ─── Memory ──────────────────────────────────────────────────────────────────

/**
 * Derive memory status from usage percentage.
 * @param {number} usagePercent
 * @returns {Status}
 */
export function memoryStatus(usagePercent) {
  if (usagePercent == null) return 'unknown';
  if (usagePercent > 85) return 'critical';
  if (usagePercent > 65) return 'warning';
  return 'good';
}

// ─── Storage ─────────────────────────────────────────────────────────────────

/**
 * Derive storage status from usage percentage.
 * @param {number} usagePercent
 * @returns {Status}
 */
export function storageStatus(usagePercent) {
  if (usagePercent == null) return 'unknown';
  if (usagePercent > 90) return 'critical';
  if (usagePercent > 70) return 'warning';
  return 'good';
}

// ─── Network ─────────────────────────────────────────────────────────────────

/**
 * Derive network status from internet connectivity.
 * @param {boolean} internetAvailable
 * @returns {Status}
 */
export function networkStatus(internetAvailable) {
  return internetAvailable ? 'good' : 'critical';
}

// ─── Health score ─────────────────────────────────────────────────────────────

/**
 * Derive a status label from a 0–100 health score.
 * @param {number} score
 * @returns {Status}
 */
export function healthScoreStatus(score) {
  if (score == null) return 'unknown';
  if (score >= 85) return 'good';
  if (score >= 65) return 'warning';
  return 'critical';
}

// ─── CSS variable helpers ─────────────────────────────────────────────────────

/**
 * Map a Status to the corresponding CSS color variable.
 * @param {Status} status
 * @returns {string}  e.g. 'var(--color-success)'
 */
export function statusColor(status) {
  switch (status) {
    case 'good':     return 'var(--color-success)';
    case 'warning':  return 'var(--color-warning)';
    case 'critical': return 'var(--color-danger)';
    default:         return 'var(--color-text-muted)';
  }
}

/**
 * Map a risk level string to a CSS color variable.
 * @param {'LOW'|'MEDIUM'|'HIGH'|'CRITICAL'} risk
 * @returns {string}
 */
export function riskColor(risk) {
  switch (risk) {
    case 'LOW':      return 'var(--color-success)';
    case 'MEDIUM':   return 'var(--color-warning)';
    case 'HIGH':     return 'var(--color-danger)';
    case 'CRITICAL': return 'var(--color-danger)';
    default:         return 'var(--color-text-muted)';
  }
}

/**
 * Map a log severity to a CSS color variable.
 * @param {'info'|'warning'|'critical'} severity
 * @returns {string}
 */
export function severityColor(severity) {
  switch (severity) {
    case 'critical': return 'var(--color-danger)';
    case 'warning':  return 'var(--color-warning)';
    case 'info':     return 'var(--color-info)';
    default:         return 'var(--color-text-muted)';
  }
}
