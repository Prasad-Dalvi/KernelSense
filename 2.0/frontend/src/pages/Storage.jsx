import React from 'react';
import { HardDrive, Sparkles } from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { useStorage } from '../hooks/useStorage';
import { useNavigate } from 'react-router-dom';
import { sound } from '../utils/soundEffects';
import styles from './Storage.module.css';

export default function Storage() {
  const { data: storage, loading, error, reload } = useStorage(2000);
  const navigate = useNavigate();

  if (loading) return <p className="text-muted pulse" style={{ padding: '24px' }}>Reading mounted volume usage...</p>;
  if (error) return <div style={{ color: 'var(--color-danger)', padding: '24px' }}>Error: {error} <button onClick={reload}>Retry</button></div>;

  const hasCapacity = Number.isFinite(storage.total_gb) && storage.total_gb > 0;
  const pieData = hasCapacity ? [
    { name: 'Used Space', value: storage.used_gb },
    { name: 'Available Space', value: storage.available_gb },
  ] : [];
  const filesystems = [...new Set(storage.partitions.map((partition) => partition.fstype).filter(Boolean))];

  return (
    <div className={styles.page}>
      <section className={`${styles.storageHero} glass-card`}>
        <div className={styles.heroLeft}>
          <div className={styles.badgeRow}>
            <span className={styles.fsPill}>
              <HardDrive size={12} /> {storage.partitions.length} MOUNTED VOLUMES
            </span>
            {filesystems.length > 0 && (
              <span className={styles.fsPill}>{filesystems.join(', ')}</span>
            )}
          </div>

          <h1 className={styles.heroTitle}>
            Disk &amp; <span className="grad-text">Drive Usage</span>
          </h1>

          <p className={styles.heroSubtitle}>
            Capacity and filesystem values reported by the host for mounted volumes.
          </p>

          <div className={styles.heroActions}>
            <button
              className="btn-primary"
              onClick={() => {
                sound.approve();
                navigate('/assistant?q=Explain%20the%20current%20disk%20usage%20on%20my%20computer');
              }}
            >
              <Sparkles size={14} />
              <span>ASK ABOUT STORAGE</span>
            </button>
          </div>
        </div>
      </section>

      <div className={`${styles.overviewCard} glass-card`}>
        {hasCapacity ? (
          <div className={styles.pieWrap}>
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%" cy="50%"
                  innerRadius={56} outerRadius={80}
                  dataKey="value"
                  startAngle={90} endAngle={-270}
                  isAnimationActive={false}
                >
                  <Cell fill="var(--color-cyan)" stroke="var(--color-bg-primary)" strokeWidth={3} />
                  <Cell fill="rgba(255,255,255,0.06)" stroke="var(--color-bg-primary)" strokeWidth={3} />
                </Pie>
                <Tooltip
                  formatter={(value) => `${value} GB`}
                  contentStyle={{ background: 'rgba(10, 14, 26, 0.95)', border: '1px solid var(--color-border-strong)', borderRadius: 8, fontSize: 12, fontFamily: 'var(--font-mono)' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className={styles.pieCenter}>
              <span className={styles.piePct}>{storage.usage}%</span>
              <span className={styles.pieLabel}>UTILIZATION</span>
            </div>
          </div>
        ) : (
          <p className={styles.noStorage}>No mounted volume capacity could be measured.</p>
        )}

        <div className={styles.statsCol}>
          <h3 className={styles.statsTitle}>Detected Volume Capacity</h3>
          <div className={styles.statGrid}>
            <StatCard label="TOTAL CAPACITY" value={formatGb(storage.total_gb)} />
            <StatCard label="USED SPACE" value={formatGb(storage.used_gb)} color="var(--color-cyan)" />
            <StatCard label="AVAILABLE SPACE" value={formatGb(storage.available_gb)} color="var(--color-emerald)" />
          </div>
        </div>
      </div>

      <section className={`${styles.section} glass-card`}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitleGroup}>
            <HardDrive size={16} color="var(--color-cyan)" />
            <h2 className={styles.sectionTitle}>Mounted Volumes</h2>
          </div>
        </div>

        {storage.partitions.length > 0 ? (
          <div className={styles.partitionTableWrap}>
            <table className={styles.partitionTable}>
              <thead>
                <tr>
                  <th>Mount point</th>
                  <th>Device</th>
                  <th>Filesystem</th>
                  <th>Used / Total</th>
                  <th>Available</th>
                  <th>Usage</th>
                </tr>
              </thead>
              <tbody>
                {storage.partitions.map((partition) => (
                  <tr key={`${partition.device}:${partition.mountpoint}`}>
                    <td>{partition.mountpoint}</td>
                    <td>{partition.device}</td>
                    <td>{partition.fstype || 'Not reported'}</td>
                    <td>{formatPair(partition.used_gb, partition.total_gb)}</td>
                    <td>{formatGb(partition.free_gb)}</td>
                    <td>{Number.isFinite(partition.percent) ? `${partition.percent}%` : 'Not reported'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className={styles.noStorage}>No mounted volumes could be measured.</p>
        )}
      </section>

      {storage.recommendations.length > 0 && (
        <section className={`${styles.section} glass-card`}>
          <div className={styles.sectionHeader}>
            <div className={styles.sectionTitleGroup}>
              <Sparkles size={16} color="var(--color-purple)" />
              <h2 className={styles.sectionTitle}>Storage Recommendations</h2>
            </div>
          </div>
          <ul className={styles.recList}>
            {storage.recommendations.map((recommendation) => (
              <li key={recommendation}>{recommendation}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function formatGb(value) {
  return Number.isFinite(value) ? `${value.toFixed(2)} GB` : 'Not reported';
}

function formatPair(used, total) {
  return Number.isFinite(used) && Number.isFinite(total)
    ? `${used.toFixed(2)} / ${total.toFixed(2)} GB`
    : 'Not reported';
}

function StatCard({ label, value, color }) {
  return (
    <div className={styles.statBox}>
      <span className={styles.statLabel}>{label}</span>
      <span className={styles.statVal} style={color ? { color } : {}}>{value}</span>
    </div>
  );
}
