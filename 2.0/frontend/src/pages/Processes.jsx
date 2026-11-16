import React, { useState, useRef } from 'react';
import { ArrowUp, ArrowDown, RefreshCw, Search, Bot } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useProcesses } from '../hooks/useProcesses';
import { useSystemStats } from '../hooks/useSystemStats';
import { sound } from '../utils/soundEffects';
import styles from './Processes.module.css';

const STATUS_COLOR = {
  running:  'var(--color-success)',
  sleeping: 'var(--color-text-muted)',
  stopped:  'var(--color-danger)',
};

export default function Processes() {
  const { processes, loading, error, reload, sortKey, sortDir, toggleSort } = useProcesses(1000);
  const { data: systemStats } = useSystemStats(1000);
  const [filterText, setFilterText] = useState('');
  const searchRef = useRef(null);
  const navigate = useNavigate();

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <span className={styles.sortPlaceholder}>⇅</span>;
    return sortDir === 'desc' ? <ArrowDown size={11} className={styles.sortActive} /> : <ArrowUp size={11} className={styles.sortActive} />;
  };

  const handleSort = (key) => {
    sound.click();
    toggleSort(key);
  };

  const handleDiagnoseProcess = (proc) => {
    sound.nav();
    navigate(`/assistant?q=Inspect%20and%20diagnose%20process%20PID%20${proc.pid}%20(${proc.name})%20consuming%20${proc.cpu_percent}%25%20CPU`);
  };

  const filteredProcesses = processes.filter(p =>
    (p.name ?? '').toLowerCase().includes(filterText.toLowerCase()) ||
    String(p.pid).includes(filterText) ||
    (p.user ?? '').toLowerCase().includes(filterText.toLowerCase())
  );

  const runningCount = processes.filter(p => p.status === 'running').length;
  const sleepingCount = processes.filter(p => p.status === 'sleeping').length;

  if (loading && !processes.length) {
    return (
      <div className={styles.loading}>
        <span className="spin" style={{ color: 'var(--color-green)' }}>◌</span>
        <span className="pulse">Reading the live process list...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorLine}>
        <span style={{ color: 'var(--color-danger)' }}>✗ ERROR: {error}</span>
        <button className={styles.retryBtn} onClick={() => { sound.click(); reload(); }}>[ RETRY ]</button>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={`${styles.telemetryHeader} hud-card`}>
        <div className={styles.teleItem}>
          <span className={styles.teleKey}>LISTED PROCESSES:</span>
          <span className={styles.teleVal}>{processes.length}</span>
        </div>
        <div className={styles.teleItem}>
          <span className={styles.teleKey}>RUNNING:</span>
          <span className={styles.teleValGreen}>{runningCount}</span>
        </div>
        <div className={styles.teleItem}>
          <span className={styles.teleKey}>SLEEPING:</span>
          <span className={styles.teleVal}>{sleepingCount}</span>
        </div>
        <div className={styles.teleItem}>
          <span className={styles.teleKey}>SWAP USED:</span>
          <span className={styles.teleVal}>
            {formatSwap(systemStats?.memory?.swap_used, systemStats?.memory?.swap_total)}
          </span>
        </div>
      </div>

      {/* ── Toolbar / Filter ── */}
      <div className={`${styles.toolbar} hud-card`}>
        <div className={styles.searchWrap}>
          <Search size={13} className={styles.searchIcon} />
          <input
            ref={searchRef}
            type="text"
            className={styles.searchInput}
            placeholder="Filter by process name, PID, or user..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
          />
          {filterText && (
            <button className={styles.clearSearchBtn} onClick={() => setFilterText('')}>✕</button>
          )}
        </div>

        <div className={styles.toolbarRight}>
          <span className={styles.matchCount}>
            {filteredProcesses.length} / {processes.length} MATCHES
          </span>
          <button className={styles.refreshBtn} onClick={() => { sound.click(); reload(); }} title="Refresh processes now">
            <RefreshCw size={11} />
            <span>REFRESH</span>
          </button>
        </div>
      </div>

      {/* ── High-Tech Process Table ── */}
      <div className={`${styles.tableWrap} hud-card`}>
        <table className={styles.table}>
          <thead>
            <tr className={styles.thead}>
              <th className={styles.th}>PID</th>
              <th className={styles.th}>COMMAND / NAME</th>
              <th
                className={`${styles.th} ${styles.sortable}`}
                onClick={() => handleSort('cpu_percent')}
                title="Sort by CPU Usage"
              >
                %CPU <SortIcon col="cpu_percent" />
              </th>
              <th
                className={`${styles.th} ${styles.sortable}`}
                onClick={() => handleSort('memory_percent')}
                title="Sort by Memory Usage"
              >
                %MEM <SortIcon col="memory_percent" />
              </th>
              <th className={styles.th}>MEMORY (RSS)</th>
              <th className={styles.th}>USER</th>
              <th className={styles.th}>STATE</th>
              <th className={styles.th} style={{ textAlign: 'right' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {filteredProcesses.map((p) => {
              const cpuColor = p.cpu_percent >= 80 ? 'var(--color-danger)' : p.cpu_percent >= 40 ? 'var(--color-warning)' : 'var(--color-text-primary)';
              const memColor = p.memory_percent >= 25 ? 'var(--color-danger)' : p.memory_percent >= 10 ? 'var(--color-warning)' : 'var(--color-text-primary)';

              return (
                <tr key={p.pid} className={styles.row}>
                  <td className={`${styles.td} ${styles.pid}`}>
                    <code>{p.pid}</code>
                  </td>
                  <td className={`${styles.td} ${styles.nameCell}`}>
                    <span className={styles.procName}>{p.name}</span>
                  </td>
                  <td className={styles.td}>
                    <div className={styles.usageWrapper}>
                      <span className={styles.usageNum} style={{ color: cpuColor, fontWeight: p.cpu_percent >= 40 ? 800 : 500 }}>
                        {formatPercent(p.cpu_percent)}
                      </span>
                      {Number.isFinite(p.cpu_percent) && <InlineBar value={p.cpu_percent} max={100} warn={40} danger={80} />}
                    </div>
                  </td>
                  <td className={styles.td}>
                    <div className={styles.usageWrapper}>
                      <span className={styles.usageNum} style={{ color: memColor, fontWeight: p.memory_percent >= 10 ? 800 : 500 }}>
                        {formatPercent(p.memory_percent)}
                      </span>
                      {Number.isFinite(p.memory_percent) && <InlineBar value={p.memory_percent} max={30} warn={10} danger={25} />}
                    </div>
                  </td>
                  <td className={`${styles.td} ${styles.mem}`}>
                    {Number.isFinite(p.memory_mb)
                      ? (p.memory_mb >= 1024 ? `${(p.memory_mb / 1024).toFixed(2)} GB` : `${p.memory_mb.toFixed(0)} MB`)
                      : 'Not reported'}
                  </td>
                  <td className={`${styles.td} ${styles.user}`}>{p.user ?? 'Not reported'}</td>
                  <td className={styles.td}>
                    <span
                      className={styles.stateBadge}
                      style={{
                        color: STATUS_COLOR[p.status] ?? 'var(--color-text-muted)',
                        borderColor: STATUS_COLOR[p.status] ?? 'var(--color-border)',
                      }}
                    >
                      {p.status ? p.status.toUpperCase() : 'NOT REPORTED'}
                    </span>
                  </td>
                  <td className={styles.td} style={{ textAlign: 'right' }}>
                    <button
                      className={styles.diagnoseBtn}
                      onClick={() => handleDiagnoseProcess(p)}
                      title={`Inspect ${p.name} with AI`}
                    >
                      <Bot size={10} />
                      <span>DIAGNOSE</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatPercent(value) {
  return Number.isFinite(value) ? `${value.toFixed(1)}%` : 'Not reported';
}

function formatSwap(used, total) {
  return Number.isFinite(used) && Number.isFinite(total)
    ? `${used.toFixed(2)} / ${total.toFixed(2)} GB`
    : 'Not reported';
}

function InlineBar({ value, max, warn, danger }) {
  const segments = 10;
  const filled = Math.min(segments, Math.max(0, Math.round((value / max) * segments)));
  const color = value >= danger ? 'var(--color-danger)' : value >= warn ? 'var(--color-warning)' : 'var(--color-green)';

  return (
    <div className={styles.inlineBarWrap}>
      {Array.from({ length: segments }).map((_, i) => (
        <span
          key={i}
          className={`${styles.miniSegment} ${i < filled ? styles.miniFilled : styles.miniEmpty}`}
          style={i < filled ? { background: color, boxShadow: i === filled - 1 ? `0 0 4px ${color}` : 'none' } : {}}
        />
      ))}
    </div>
  );
}
