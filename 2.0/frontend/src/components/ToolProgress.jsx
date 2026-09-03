import React from 'react';
import { CheckCircle, Circle, Loader } from 'lucide-react';
import styles from './ToolProgress.module.css';

/**
 * Terminal-style AI tool execution progress.
 */
export default function ToolProgress({ steps = [], analyzing = false }) {
  if (!steps.length && !analyzing) return null;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={`${styles.spinner} ${analyzing ? 'spin' : ''}`}>
          {analyzing ? '◌' : '✓'}
        </span>
        <span className={styles.headerText}>
          {analyzing ? 'kernelsense is analyzing...' : 'analysis complete'}
        </span>
      </div>
      {steps.map((step, i) => (
        <div key={i} className={styles.step}>
          <span className={styles.stepIcon}>
            {step.status === 'done'
              ? <span className={styles.done}>✓</span>
              : step.status === 'active'
              ? <span className={`${styles.active} pulse`}>▸</span>
              : <span className={styles.pending}>○</span>
            }
          </span>
          <span className={`${styles.stepLabel} ${step.status === 'done' ? styles.labelDone : step.status === 'active' ? styles.labelActive : styles.labelPending}`}>
            {step.label}
          </span>
          {step.status === 'active' && (
            <span className={`${styles.working} pulse`}>...</span>
          )}
        </div>
      ))}
    </div>
  );
}
