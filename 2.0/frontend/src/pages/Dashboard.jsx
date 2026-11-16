import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cpu, MemoryStick, HardDrive, Wifi, Activity,
  Sparkles, RefreshCw, ShieldCheck, ArrowRight,
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, Tooltip, YAxis,
} from 'recharts';
import { useSystemStats } from '../hooks/useSystemStats';
import { useHostInfo } from '../hooks/useHostInfo';
import { fetchEvents } from '../api/eventsApi';
import { cpuStatus, memoryStatus, storageStatus, networkStatus } from '../utils/statusHelpers';
import { sound } from '../utils/soundEffects';
import StatusCard from '../components/StatusCard';
import Timeline from '../components/Timeline';
import styles from './Dashboard.module.css';

function useEvents(autoRefreshMs = 3000) {
  const [events, setEvents] = useState([]);
  const [evLoading, setEvLoading] = useState(true);
  const [evError, setEvError] = useState(null);

  const load = async () => {
    try {
      setEvents(await fetchEvents({ limit: 10 }));
      setEvError(null);
    } catch (error) {
      setEvError(error?.message ?? 'Failed to load host events.');
    } finally {
      setEvLoading(false);
    }
  };

  useEffect(() => {
    load();
    if (autoRefreshMs > 0) {
      const id = setInterval(load, autoRefreshMs);
      return () => clearInterval(id);
    }
  }, [autoRefreshMs]);

  return { events, evLoading, evError, reload: load };
}

const CustomGlassTooltip = ({ active, payload, prefix, color }) => {
  if (!active || !payload?.length) return null;
  const rawVal = payload[0]?.value;
  if (typeof rawVal !== 'number' || !Number.isFinite(rawVal)) return null;
  const numVal = rawVal;
  return (
    <div className={styles.chartTooltip}>
      <span className={styles.tooltipLabel}>{prefix} LOAD</span>
      <span className={styles.tooltipVal} style={{ color: color || 'var(--color-cyan)' }}>
        {numVal.toFixed(1)}%
      </span>
    </div>
  );
};

export default function Dashboard() {
  const { data, loading, error, reload } = useSystemStats(1000);
  const { data: hostInfo } = useHostInfo();
  const { events, evLoading, evError, reload: reloadEvents } = useEvents(5000);
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className={styles.loadingState}>
        <div className={`${styles.loadingBox} glass-card`}>
          <span className="spin" style={{ color: 'var(--color-cyan)', fontSize: 20 }}>◌</span>
          <span>Reading live host metrics...</span>
        </div>
      </div>
    );
  }

  if (error) return <ErrorState message={error} onRetry={reload} />;

  const { cpu, memory, storage, network, health } = data;

  const cpuHistory = Array.isArray(cpu?.history) ? cpu.history : [];
  const memHistory = Array.isArray(memory?.history) ? memory.history : [];
  const activeInterface = network.interfaces.find((iface) => iface.ip && iface.type !== 'loopback');
  const cpuDetails = [
    cpu.cores ? `${cpu.cores} cores` : null,
    hostInfo?.cpu_frequency_mhz ? `${(hostInfo.cpu_frequency_mhz / 1000).toFixed(2)} GHz` : null,
  ].filter(Boolean).join(' · ');

  const cpuSt = cpuStatus(cpu.usage);
  const memSt = memoryStatus(memory.usage);
  const stoSt = storageStatus(storage.usage);
  const netSt = networkStatus(network.internet);

  const handleLaunchAI = () => {
    sound.approve();
    navigate('/assistant?q=Run%20a%20full%20system%20health%20and%20performance%20diagnosis');
  };

  return (
    <div className={styles.page}>
      {/* ── 1. Hero Quantum CPU Telemetry Banner ── */}
      <section className={`${styles.heroBanner} glass-card`}>
        <div className={styles.heroContent}>
          <div className={styles.heroBadgeRow}>
            {hostInfo?.os_name && (
              <span className={styles.systemPill}>
                <span className={styles.pulseDot} /> {hostInfo.os_name}
              </span>
            )}
            {cpuDetails && (
              <span className={styles.specPill}>
                <Cpu size={12} /> {cpuDetails}
              </span>
            )}
            {hostInfo && (
              <span className={styles.specPill}>
                UPTIME: {formatUptime(hostInfo.uptime_seconds)}
              </span>
            )}
          </div>

          <h1 className={styles.heroTitle}>
            Kernel Operations <span className="grad-text">Command Center</span>
          </h1>
          <p className={styles.heroSubtitle}>
            Live host resource metrics, network status, and events collected from the operating system.
          </p>

          <div className={styles.heroActions}>
            <button className="btn-primary" onClick={handleLaunchAI}>
              <Sparkles size={15} />
              <span>LAUNCH AI DIAGNOSTIC</span>
            </button>
            <button
              className={styles.secondaryBtn}
              onClick={() => { sound.nav(); navigate('/processes'); }}
            >
              <span>INSPECT PROCESSES</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>

      </section>

      {/* ── 2. Top Metric Cards ── */}
      <section className={styles.cardsGrid}>
        <StatusCard
          title="CPU Telemetry"
          value={cpu.usage}
          unit="%"
          subtitle={cpuDetails || undefined}
          status={cpuSt}
          icon={Cpu}
        />
        <StatusCard
          title="RAM Utilization"
          value={memory.usage}
          unit="%"
          subtitle={formatCapacity(memory.used_gb, memory.total_gb)}
          status={memSt}
          icon={MemoryStick}
        />
        <StatusCard
          title="Storage Buffer"
          value={storage.usage}
          unit="%"
          subtitle={formatCapacity(storage.used_gb, storage.total_gb)}
          status={stoSt}
          icon={HardDrive}
        />
        <StatusCard
          title="Network Gateway"
          value={network.internet == null ? null : network.internet ? 'Online' : 'Offline'}
          subtitle={activeInterface ? `${activeInterface.name}: ${activeInterface.ip}` : undefined}
          status={netSt}
          icon={Wifi}
        />
      </section>

      {/* ── 3. Tri-Pane Telemetry Suite ── */}
      <div className={styles.triPaneGrid}>
        {/* Left: Health Score Centerpiece */}
        <section className={`${styles.healthPanel} glass-card`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitleGroup}>
              <ShieldCheck size={16} className={styles.headerIconCyan} />
              <h2 className={styles.panelTitle}>System Health Index</h2>
            </div>
            <span className={styles.activeTag}>LIVE</span>
          </div>

          <div className={styles.healthScoreCenter}>
            <div className={styles.gaugeContainer}>
              <svg viewBox="0 0 120 120" className={styles.gaugeSvg}>
                <defs>
                  <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--color-cyan)" />
                    <stop offset="50%" stopColor="var(--color-purple)" />
                    <stop offset="100%" stopColor="var(--color-emerald)" />
                  </linearGradient>
                </defs>
                <circle cx="60" cy="60" r="50" stroke="rgba(255,255,255,0.06)" strokeWidth="8" fill="none" />
                <circle
                  cx="60" cy="60" r="50"
                  stroke="url(#scoreGrad)"
                  strokeWidth="8"
                  strokeDasharray={`${(health.score / 100) * 314} 314`}
                  strokeLinecap="round"
                  fill="none"
                  transform="rotate(-90 60 60)"
                  style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.16, 1, 0.3, 1)' }}
                />
              </svg>
              <div className={styles.gaugeCenterText}>
                <span className={styles.scoreNumber}>{health.score}</span>
                <span className={styles.scoreOutOf}>/ 100</span>
              </div>
            </div>

            <span className={styles.healthStatusText}>
              {health.score >= 85 ? '✓ EXCELLENT PERFORMANCE' : health.score >= 70 ? '⚠ OPTIMIZATION RECOMMENDED' : '✗ CRITICAL WARNING'}
            </span>
          </div>

          <div className={styles.categoriesList}>
            {health.categories.map((cat) => {
              const hasScore = Number.isFinite(cat.score);
              const color = !hasScore
                ? 'var(--color-text-muted)'
                : cat.score >= 85
                ? 'var(--color-emerald)'
                : cat.score >= 70
                ? 'var(--color-amber)'
                : 'var(--color-rose)';
              return (
                <div key={cat.name} className={styles.catRow}>
                  <div className={styles.catHeader}>
                    <span className={styles.catName}>{cat.name}</span>
                    <span className={styles.catScore} style={{ color }}>{hasScore ? `${cat.score}%` : '—'}</span>
                  </div>
                  <div className={styles.catProgressBg}>
                    <div className={styles.catProgressFill} style={{ width: hasScore ? `${cat.score}%` : '0%', background: color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Center: Live Oscilloscope History Area Charts */}
        <section className={`${styles.chartPanel} glass-card`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitleGroup}>
              <Cpu size={16} className={styles.headerIconCyan} />
              <h2 className={styles.panelTitle}>CPU Live Oscilloscope</h2>
            </div>
            <span className={styles.statRate}>1 SEC REFRESH</span>
          </div>

          <div className={styles.chartAreaWrap}>
            {cpuHistory.length > 0 ? <ResponsiveContainer width="100%" height={110} minWidth={0}>
              <AreaChart data={cpuHistory} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="cpuAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-cyan)" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="var(--color-cyan)" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <YAxis domain={[0, 100]} hide />
                <Tooltip content={<CustomGlassTooltip prefix="CPU" color="var(--color-cyan)" />} />
                <Area type="monotone" dataKey="value" stroke="var(--color-cyan)" strokeWidth={2}
                  fill="url(#cpuAreaGrad)" dot={false} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer> : <p className={styles.eventsLoading}>No CPU samples received.</p>}
          </div>

          <div className={styles.panelHeader} style={{ marginTop: 18 }}>
            <div className={styles.panelTitleGroup}>
              <MemoryStick size={16} className={styles.headerIconPurple} />
              <h2 className={styles.panelTitle}>Memory Usage History</h2>
            </div>
            <span className={styles.statRate}>RAM</span>
          </div>

          <div className={styles.chartAreaWrap}>
            {memHistory.length > 0 ? <ResponsiveContainer width="100%" height={110} minWidth={0}>
              <AreaChart data={memHistory} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="memAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-purple)" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="var(--color-purple)" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <YAxis domain={[0, 100]} hide />
                <Tooltip content={<CustomGlassTooltip prefix="MEM" color="var(--color-purple)" />} />
                <Area type="monotone" dataKey="value" stroke="var(--color-purple)" strokeWidth={2}
                  fill="url(#memAreaGrad)" dot={false} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer> : <p className={styles.eventsLoading}>No memory samples received.</p>}
          </div>
        </section>

        {/* Right: Kernel Events Timeline Stream */}
        <section className={`${styles.eventsPanel} glass-card`}>
          <div className={styles.panelHeader} style={{ padding: '16px 20px 8px' }}>
            <div className={styles.panelTitleGroup}>
              <Activity size={16} className={styles.headerIconCyan} />
              <h2 className={styles.panelTitle}>System Events</h2>
            </div>
            <button className={styles.refreshBtn} onClick={() => { sound.click(); reloadEvents(); }} title="Refresh Events">
              <RefreshCw size={12} />
            </button>
          </div>

          <div className={styles.eventsScroll}>
            {evLoading ? (
              <p className={styles.eventsLoading}>Reading host events...</p>
            ) : evError ? (
              <p className={styles.eventsLoading}>Unable to read host events: {evError}</p>
            ) : (
              <Timeline events={events} />
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function formatCapacity(used, total) {
  if (used == null || total == null) return undefined;
  return `${used.toFixed(1)} / ${total.toFixed(1)} GB used`;
}

function formatUptime(seconds) {
  if (typeof seconds !== 'number' || !Number.isFinite(seconds)) return null;
  const totalHours = Math.floor(seconds / 3600);
  const days = Math.floor(totalHours / 24);
  const hours = totalHours % 24;
  return days > 0 ? `${days}d ${hours}h` : `${hours}h`;
}

function ErrorState({ message, onRetry }) {
  return (
    <div className={styles.errorState}>
      <p>Error connecting to backend: {message}</p>
      <button className="btn-primary" onClick={onRetry}>Retry</button>
    </div>
  );
}
