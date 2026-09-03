import React from 'react';
import { Activity, CheckCircle, AlertCircle, AlertTriangle, Sparkles, ShieldCheck, ArrowRight, Server, Cpu, Database } from 'lucide-react';
import { useSystemStats } from '../hooks/useSystemStats';
import { useNavigate } from 'react-router-dom';
import { sound } from '../utils/soundEffects';
import datacenterImg from '../assets/cyber_datacenter.jpg';
import styles from './SystemHealth.module.css';

const STATUS_MAP = {
  good:            { label: 'OPTIMAL',    icon: CheckCircle,   cls: styles.good,    color: 'var(--color-emerald)' },
  needs_attention: { label: 'ATTENTION',  icon: AlertTriangle, cls: styles.warn,    color: 'var(--color-amber)'   },
  critical:        { label: 'CRITICAL',   icon: AlertCircle,   cls: styles.danger,  color: 'var(--color-rose)'    },
  unknown:         { label: 'UNKNOWN',    icon: Activity,      cls: styles.neutral, color: 'var(--color-text-muted)' },
};

export default function SystemHealth() {
  const { data, loading, error, reload } = useSystemStats(1000);
  const navigate = useNavigate();

  if (loading) return <p className="text-muted pulse" style={{ padding: '24px' }}>Auditing kernel subsystems &amp; hardware thermals...</p>;
  if (error) return <div style={{ color: 'var(--color-danger)', padding: '24px' }}>Error: {error} <button onClick={reload}>Retry</button></div>;

  const { health } = data;

  const handleFixCategory = (cat) => {
    sound.nav();
    navigate(`/assistant?q=Provide%20remediation%20and%20root%20cause%20analysis%20for%20subsystem:%20${encodeURIComponent(cat.name)}%20(${cat.explanation})`);
  };

  return (
    <div className={styles.page}>
      {/* ── 1. Hero Datacenter Health Banner ── */}
      <section className={`${styles.healthHero} glass-card`}>
        <div className={styles.heroLeft}>
          <div className={styles.badgeRow}>
            <span className={styles.healthScorePill}>
              <ShieldCheck size={13} /> HEALTH SCORE: {health.score}/100
            </span>
            <span className={styles.subsystemPill}>
              <Server size={12} /> 6 SUBSYSTEMS MONITORED
            </span>
          </div>

          <h1 className={styles.heroTitle}>
            Kernel &amp; Subsystem <span className="grad-text">Health Audit</span>
          </h1>

          <p className={styles.heroSubtitle}>
            Continuous hardware thermal monitoring, eBPF scheduler analysis, memory leak detection, and automatic remediation recommendations.
          </p>

          <div className={styles.heroActions}>
            <button
              className="btn-primary"
              onClick={() => {
                sound.approve();
                navigate('/assistant?q=Perform%20full%20system%20health%20audit%20and%20auto-fix%20recommendations');
              }}
            >
              <Sparkles size={14} />
              <span>RUN FULL AI DIAGNOSTIC</span>
            </button>
          </div>
        </div>

        <div className={styles.heroImgWrap}>
          <img src={datacenterImg} alt="Linux Datacenter" className={styles.heroImg} />
        </div>
      </section>

      {/* ── 2. Master Radial Score Card ── */}
      <div className={`${styles.masterScoreCard} glass-card`}>
        <div className={styles.scoreGaugeWrap}>
          <svg viewBox="0 0 120 120" className={styles.gaugeSvg}>
            <defs>
              <linearGradient id="hlthGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="var(--color-cyan)" />
                <stop offset="100%" stopColor="var(--color-emerald)" />
              </linearGradient>
            </defs>
            <circle cx="60" cy="60" r="50" stroke="rgba(255,255,255,0.06)" strokeWidth="8" fill="none" />
            <circle
              cx="60" cy="60" r="50"
              stroke="url(#hlthGrad)"
              strokeWidth="8"
              strokeDasharray={`${(health.score / 100) * 314} 314`}
              strokeLinecap="round"
              fill="none"
              transform="rotate(-90 60 60)"
              style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.16, 1, 0.3, 1)' }}
            />
          </svg>
          <div className={styles.gaugeText}>
            <span className={styles.gaugeScoreNum}>{health.score}</span>
            <span className={styles.gaugeMax}>/ 100</span>
          </div>
        </div>

        <div className={styles.scoreSummary}>
          <h3 className={styles.scoreTitle}>
            {health.score >= 90 ? 'All Systems Operating Nominally' :
             health.score >= 75 ? 'Healthy with Minor Optimization Suggestions' :
             'Degraded Subsystem Performance Detected'}
          </h3>
          <p className={styles.scoreDesc}>
            Real-time telemetry gathered across CPU load balancing, swap pressure, disk I/O throughput, socket latency, and security firewall policies.
          </p>
        </div>
      </div>

      {/* ── 3. Subsystem Breakdown Grid ── */}
      <div className={styles.grid}>
        {health.categories.map((cat) => {
          const cfg = STATUS_MAP[cat.status] ?? STATUS_MAP.unknown;
          const Icon = cfg.icon;

          return (
            <div key={cat.name} className={`${styles.catCard} ${cfg.cls} glass-card`}>
              <div className={styles.catHeader}>
                <div className={styles.catTitleGroup}>
                  <span className={styles.catName}>{cat.name}</span>
                  <span className={styles.catStatusPill} style={{ color: cfg.color, borderColor: cfg.color }}>
                    <Icon size={11} />
                    {cfg.label}
                  </span>
                </div>
                <span className={styles.catScoreNum} style={{ color: cfg.color }}>{cat.score}%</span>
              </div>

              <div className={styles.barWrap}>
                <div className={styles.barFill} style={{ width: `${cat.score}%`, background: cfg.color }} />
              </div>

              <p className={styles.explanation}>{cat.explanation}</p>

              {cat.recommendation && (
                <div className={styles.recBox}>
                  <Sparkles size={12} color="var(--color-cyan)" />
                  <span>{cat.recommendation}</span>
                </div>
              )}

              <button className={styles.remediateBtn} onClick={() => handleFixCategory(cat)}>
                <span>AI REMEDIATE // REASONING</span>
                <ArrowRight size={12} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
