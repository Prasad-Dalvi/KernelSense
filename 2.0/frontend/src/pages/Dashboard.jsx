import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cpu, MemoryStick, HardDrive, Wifi, Activity,
  Sparkles, RefreshCw, Terminal, ShieldCheck, Zap,
  CheckCircle, ArrowRight, Layers,
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, Tooltip, YAxis,
} from 'recharts';
import { useSystemStats } from '../hooks/useSystemStats';
import { fetchEvents } from '../api/eventsApi';
import { cpuStatus, memoryStatus, storageStatus, networkStatus } from '../utils/statusHelpers';
import { sound } from '../utils/soundEffects';
import StatusCard from '../components/StatusCard';
import Timeline from '../components/Timeline';
import quantumCpuImg from '../assets/quantum_cpu.jpg';
import styles from './Dashboard.module.css';

function useEvents(autoRefreshMs = 3000) {
  const [events, setEvents] = useState([]);
  const [evLoading, setEvLoading] = useState(true);

  const load = () => {
    fetchEvents({ limit: 10 })
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setEvLoading(false));
  };

  useEffect(() => {
    load();
    if (autoRefreshMs > 0) {
      const id = setInterval(load, autoRefreshMs);
      return () => clearInterval(id);
    }
  }, [autoRefreshMs]);

  return { events, evLoading, reload: load };
}

const CustomGlassTooltip = ({ active, payload, label, prefix, color }) => {
  if (!active || !payload?.length) return null;
  const rawVal = payload[0]?.value;
  const numVal = typeof rawVal === 'number' ? rawVal : Number(rawVal) || 0;
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
  const { events, evLoading } = useEvents(3000);
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className={styles.loadingState}>
        <div className={`${styles.loadingBox} glass-card`}>
          <span className="spin" style={{ color: 'var(--color-cyan)', fontSize: 20 }}>◌</span>
          <span>Gathering real-time kernel telemetry &amp; device statistics...</span>
        </div>
      </div>
    );
  }

  if (error) return <ErrorState message={error} onRetry={reload} />;

  const { cpu, memory, storage, network, health } = data;

  const cpuHistory = (Array.isArray(cpu?.history) && cpu.history.length > 0)
    ? cpu.history.map((h, i) => (typeof h === 'number' ? { time: `${i}`, value: h } : (h?.value !== undefined ? { time: h.time ?? `${i}`, value: Number(h.value) || 0 } : { time: `${i}`, value: Number(h) || cpu.usage })))
    : Array.from({ length: 15 }, (_, i) => ({ time: `${i}`, value: cpu?.usage || 0 }));

  const memHistory = (Array.isArray(memory?.history) && memory.history.length > 0)
    ? memory.history.map((h, i) => (typeof h === 'number' ? { time: `${i}`, value: h } : (h?.value !== undefined ? { time: h.time ?? `${i}`, value: Number(h.value) || 0 } : { time: `${i}`, value: Number(h) || memory.usage })))
    : Array.from({ length: 15 }, (_, i) => ({ time: `${i}`, value: memory?.usage || 0 }));

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
            <span className={styles.systemPill}>
              <span className={styles.pulseDot} /> LINUX 6.8.0-GENERIC #45-UBUNTU
            </span>
            <span className={styles.specPill}>
              <Cpu size={12} /> {cpu.cores} CORES · 3.60 GHz
            </span>
            <span className={styles.specPill}>
              <Zap size={12} /> UPTIME: 14D 08H
            </span>
          </div>

          <h1 className={styles.heroTitle}>
            Kernel Operations <span className="grad-text">Command Center</span>
          </h1>
          <p className={styles.heroSubtitle}>
            Autonomous AI diagnostics, real-time eBPF monitoring, and sub-millisecond hardware telemetry orchestration.
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

        <div className={styles.heroImageWrap}>
          <img
            src={quantumCpuImg}
            alt="Quantum Hardware Telemetry"
            className={styles.heroImg}
          />
          <div className={styles.heroImageOverlay} />
        </div>
      </section>

      {/* ── 2. Top Metric Cards ── */}
      <section className={styles.cardsGrid}>
        <StatusCard
          title="CPU Telemetry"
          value={cpu.usage}
          unit="%"
          subtitle={`${cpu.cores} Cores · ${cpu.temperature ?? '42'}°C Core Temp`}
          status={cpuSt}
          icon={Cpu}
          trend={1.2}
        />
        <StatusCard
          title="RAM Utilization"
          value={memory.usage}
          unit="%"
          subtitle={`${memory.used_gb.toFixed(1)} / ${memory.total_gb} GB Used`}
          status={memSt}
          icon={MemoryStick}
          trend={-0.6}
        />
        <StatusCard
          title="Storage Buffer"
          value={storage.usage}
          unit="%"
          subtitle={`${storage.used_gb} GB Used / ${storage.total_gb} GB Total`}
          status={stoSt}
          icon={HardDrive}
          trend={0.1}
        />
        <StatusCard
          title="Network Gateway"
          value={network.internet ? 'Online' : 'Offline'}
          subtitle={`IP: ${network.interfaces[0]?.ip ?? '192.168.1.105'}`}
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
              const color = cat.score >= 85
                ? 'var(--color-emerald)'
                : cat.score >= 70
                ? 'var(--color-amber)'
                : 'var(--color-rose)';
              return (
                <div key={cat.name} className={styles.catRow}>
                  <div className={styles.catHeader}>
                    <span className={styles.catName}>{cat.name}</span>
                    <span className={styles.catScore} style={{ color }}>{cat.score}%</span>
                  </div>
                  <div className={styles.catProgressBg}>
                    <div className={styles.catProgressFill} style={{ width: `${cat.score}%`, background: color }} />
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
            <span className={styles.statRate}>100ms SAMPLING</span>
          </div>

          <div className={styles.chartAreaWrap}>
            <ResponsiveContainer width="100%" height={110} minWidth={0}>
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
            </ResponsiveContainer>
          </div>

          <div className={styles.panelHeader} style={{ marginTop: 18 }}>
            <div className={styles.panelTitleGroup}>
              <MemoryStick size={16} className={styles.headerIconPurple} />
              <h2 className={styles.panelTitle}>Memory Buffer Allocation</h2>
            </div>
            <span className={styles.statRate}>ACTIVE + SWAP</span>
          </div>

          <div className={styles.chartAreaWrap}>
            <ResponsiveContainer width="100%" height={110} minWidth={0}>
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
            </ResponsiveContainer>
          </div>
        </section>

        {/* Right: Kernel Events Timeline Stream */}
        <section className={`${styles.eventsPanel} glass-card`}>
          <div className={styles.panelHeader} style={{ padding: '16px 20px 8px' }}>
            <div className={styles.panelTitleGroup}>
              <Activity size={16} className={styles.headerIconCyan} />
              <h2 className={styles.panelTitle}>Kernel Journal Events</h2>
            </div>
            <button className={styles.refreshBtn} onClick={() => { sound.click(); reload(); }} title="Refresh Events">
              <RefreshCw size={12} />
            </button>
          </div>

          <div className={styles.eventsScroll}>
            {evLoading ? (
              <p className={styles.eventsLoading}>Fetching event journal...</p>
            ) : (
              <Timeline events={events} />
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div className={styles.errorState}>
      <p>Error connecting to backend: {message}</p>
      <button className="btn-primary" onClick={onRetry}>Retry</button>
    </div>
  );
}
