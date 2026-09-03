import React from 'react';
import styles from './Timeline.module.css';

const SEV_CLASS = {
  critical: styles.critical,
  warning:  styles.warning,
  info:     styles.info,
};

/**
 * Reusable event timeline.
 * @param {{ events: Array<{id, timestamp, title, description, severity, source}> }} props
 */
export default function Timeline({ events = [] }) {
  if (!events.length) {
    return <p className={styles.empty}>No events recorded.</p>;
  }

  return (
    <div className={styles.timeline}>
      {events.map((ev, i) => (
        <div key={ev.id ?? i} className={styles.event}>
          <div className={styles.left}>
            <div className={`${styles.dot} ${SEV_CLASS[ev.severity] ?? styles.info}`} />
            {i < events.length - 1 && <div className={styles.line} />}
          </div>
          <div className={styles.body}>
            <div className={styles.meta}>
              <span className={styles.time}>{ev.timestamp}</span>
              {ev.source && <span className={styles.source}>{ev.source}</span>}
              <span className={`${styles.badge} ${SEV_CLASS[ev.severity] ?? styles.info}`}>
                {ev.severity}
              </span>
            </div>
            <p className={styles.title}>{ev.title}</p>
            {ev.description && <p className={styles.desc}>{ev.description}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}
