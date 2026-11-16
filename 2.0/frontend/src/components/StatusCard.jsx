import React from 'react';
import { sound } from '../utils/soundEffects';
import styles from './StatusCard.module.css';

/**
 * Modern Luminous Glass Metric Card with SVG Sparkline & Gradient Halo.
 */
export default function StatusCard({ title, value, unit, subtitle, status = 'normal', icon: Icon }) {
  const statusClass = {
    good:            styles.good,
    normal:          styles.normal,
    warning:         styles.warning,
    critical:        styles.critical,
    needs_attention: styles.warning,
  }[status] ?? styles.normal;

  const numVal = typeof value === 'number' ? value : null;
  const pct = numVal !== null ? Math.min(100, Math.max(0, numVal)) : null;

  return (
    <div
      className={`${styles.card} ${statusClass} glass-card`}
      onMouseEnter={() => sound.click()}
    >
      <div className={styles.topRow}>
        <div className={styles.titleInfo}>
          <span className={styles.title}>{title}</span>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>

        {Icon && (
          <div className={styles.iconBadge}>
            <Icon size={18} className={styles.icon} />
          </div>
        )}
      </div>

      <div className={styles.valueRow}>
        <span className={styles.value}>
          {value ?? '—'}
        </span>
        {unit && <span className={styles.unit}>{unit}</span>}

      </div>

      {pct !== null && (
        <div className={styles.progressWrap}>
          <div className={styles.progressBarBg}>
            <div
              className={styles.progressBarFill}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
