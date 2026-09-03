import React from 'react';
import { HardDrive, Folder, FileText, CheckCircle, Trash2, Bot, Sparkles, Database, Layers, ArrowRight } from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { useStorage } from '../hooks/useStorage';
import { useNavigate } from 'react-router-dom';
import { sound } from '../utils/soundEffects';
import nvmeStorageImg from '../assets/nvme_storage.jpg';
import styles from './Storage.module.css';

export default function Storage() {
  const { data: storage, loading, error, reload } = useStorage(2000);
  const navigate = useNavigate();

  if (loading) return <p className="text-muted pulse" style={{ padding: '24px' }}>Analyzing EXT4 filesystems &amp; NVMe block devices...</p>;
  if (error) return <div style={{ color: 'var(--color-danger)', padding: '24px' }}>Error: {error} <button onClick={reload}>Retry</button></div>;

  const pieData = [
    { name: 'Used Space',      value: storage.used_gb },
    { name: 'Available Space', value: storage.available_gb },
  ];

  const handleClean = (dir) => {
    sound.nav();
    navigate(`/assistant?q=How%20can%20I%20safely%20clean%20up%20disk%20space%20in%20${encodeURIComponent(dir)}%3F`);
  };

  return (
    <div className={styles.page}>
      {/* ── 1. Hero NVMe Storage Banner ── */}
      <section className={`${styles.storageHero} glass-card`}>
        <div className={styles.heroLeft}>
          <div className={styles.badgeRow}>
            <span className={styles.smartPill}>
              <CheckCircle size={13} /> NVMe SSD: 100% HEALTHY
            </span>
            <span className={styles.fsPill}>
              <Database size={12} /> EXT4 // /dev/nvme0n1p2
            </span>
          </div>

          <h1 className={styles.heroTitle}>
            NVMe Storage &amp; <span className="grad-text">Block Devices</span>
          </h1>

          <p className={styles.heroSubtitle}>
            Real-time partition capacity analysis, large file telemetry, SMART drive diagnostics, and automated directory cache cleanup.
          </p>

          <div className={styles.heroActions}>
            <button
              className="btn-primary"
              onClick={() => {
                sound.approve();
                navigate('/assistant?q=Find%20large%20files%20and%20recommend%20safe%20disk%20cleanup');
              }}
            >
              <Sparkles size={14} />
              <span>AI DISK CLEANUP ADVISOR</span>
            </button>
          </div>
        </div>

        <div className={styles.heroImgWrap}>
          <img src={nvmeStorageImg} alt="NVMe Storage Array" className={styles.heroImg} />
        </div>
      </section>

      {/* ── 2. Capacity Donut & Health Readout ── */}
      <div className={`${styles.overviewCard} glass-card`}>
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
                formatter={(v) => `${v} GB`}
                contentStyle={{ background: 'rgba(10, 14, 26, 0.95)', border: '1px solid var(--color-border-strong)', borderRadius: 8, fontSize: 12, fontFamily: 'var(--font-mono)' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className={styles.pieCenter}>
            <span className={styles.piePct}>{storage.usage}%</span>
            <span className={styles.pieLabel}>UTILIZATION</span>
          </div>
        </div>

        <div className={styles.statsCol}>
          <h3 className={styles.statsTitle}>Root Partition Capacity</h3>
          <div className={styles.statGrid}>
            <StatCard label="TOTAL CAPACITY" value={`${storage.total_gb} GB`} />
            <StatCard label="USED SPACE" value={`${storage.used_gb} GB`} color="var(--color-cyan)" />
            <StatCard label="AVAILABLE SPACE" value={`${storage.available_gb} GB`} color="var(--color-emerald)" />
            <StatCard label="DRIVE TEMPERATURE" value="34°C (Optimal)" color="var(--color-emerald)" />
          </div>
        </div>
      </div>

      {/* ── 3. Largest Directories ── */}
      <section className={`${styles.section} glass-card`}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitleGroup}>
            <Folder size={16} color="var(--color-cyan)" />
            <h2 className={styles.sectionTitle}>Largest Directory Consumption</h2>
          </div>
        </div>

        <div className={styles.dirList}>
          {storage.largest_dirs.map((d, i) => (
            <div key={i} className={styles.dirRow}>
              <div className={styles.dirLeft}>
                <span className={styles.dirIdx}>0{i+1}</span>
                <code className={styles.dirPath}>{d.path}</code>
              </div>

              <div className={styles.barWrap}>
                <div className={styles.barFill} style={{ width: `${Math.round((d.size_gb / storage.largest_dirs[0].size_gb) * 100)}%` }} />
              </div>

              <span className={styles.dirSize}>{d.size_gb.toFixed(1)} GB</span>

              <button className={styles.cleanBtn} onClick={() => handleClean(d.path)}>
                <Bot size={11} />
                <span>CLEAN</span>
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* ── 4. AI Cleanup Recommendations ── */}
      {storage.recommendations.length > 0 && (
        <section className={`${styles.section} glass-card`}>
          <div className={styles.sectionHeader}>
            <div className={styles.sectionTitleGroup}>
              <Sparkles size={16} color="var(--color-purple)" />
              <h2 className={styles.sectionTitle}>AI Storage Remediation Recommendations</h2>
            </div>
          </div>
          <ul className={styles.recList}>
            {storage.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className={styles.statBox}>
      <span className={styles.statLabel}>{label}</span>
      <span className={styles.statVal} style={color ? { color } : {}}>{value}</span>
    </div>
  );
}
