import React, { useState, useEffect } from 'react';
import { ChevronRight, Terminal, Play, Copy, Check } from 'lucide-react';
import { fetchHistory } from '../api/historyApi';
import { useNavigate } from 'react-router-dom';
import { sound } from '../utils/soundEffects';
import styles from './History.module.css';

const RISK_ICON = {
  LOW:      <span className={styles.riskLow}>○ LOW RISK</span>,
  MEDIUM:   <span className={styles.riskMed}>◑ MED RISK</span>,
  HIGH:     <span className={styles.riskHigh}>● HIGH RISK</span>,
  CRITICAL: <span className={styles.riskCrit}>⚠ CRITICAL</span>,
};

export default function History() {
  const [items, setItems]       = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [selected, setSelected] = useState(null);
  const [copiedCmd, setCopiedCmd] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory()
      .then(res => {
        setItems(res);
        if (res.length > 0) setSelected(res[0]);
      })
      .catch((err) => setError(err?.message ?? 'Failed to load assistant history.'))
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = (item) => {
    sound.click();
    setSelected(item);
  };

  const handleRerun = (query) => {
    sound.nav();
    navigate(`/assistant?q=${encodeURIComponent(query)}`);
  };

  const handleCopyCmd = (cmd, idx) => {
    sound.click();
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(idx);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  if (loading) return <p className="text-muted pulse" style={{ padding: '20px' }}>Loading saved assistant history...</p>;
  if (error) return <p role="alert" style={{ color: 'var(--color-danger)', padding: '20px' }}>Unable to load assistant history: {error}</p>;

  return (
    <div className={styles.page}>
      {/* ── Left Item List ── */}
      <div className={`${styles.list} hud-card`}>
        <div className={styles.listHeader}>
          <Terminal size={12} className={styles.termIcon} />
          <span>ASSISTANT_HISTORY</span>
          <span className={styles.sessionCount}>({items.length})</span>
        </div>

        {items.length === 0 ? (
          <p className={styles.empty}>No assistant history is stored.</p>
        ) : (
          items.map((item) => {
            const isSelected = selected?.id === item.id;
            return (
              <button
                key={item.id}
                className={`${styles.item} ${isSelected ? styles.selectedItem : ''}`}
                onClick={() => handleSelect(item)}
              >
                <div className={styles.itemLeft}>
                  <div className={styles.itemTop}>
                    <Terminal size={12} color="var(--color-text-muted)" />
                    <span className={styles.query}>{item.query}</span>
                  </div>
                  <div className={styles.itemMeta}>
                    <span className={styles.time}>{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    <span className={styles.intentTag}>{item.intent}</span>
                    {RISK_ICON[item.risk_level]}
                  </div>
                </div>
                <ChevronRight size={13} className={`${styles.chevron} ${isSelected ? styles.chevronOpen : ''}`} />
              </button>
            );
          })
        )}
      </div>

      {/* ── Right Detail Telemetry Panel ── */}
      <div className={`${styles.detail} hud-card`}>
        {selected ? (
          <>
            <div className={styles.detailHeader}>
              <div className={styles.detailTitleGroup}>
                <h3 className={styles.detailTitle}>{selected.query}</h3>
                <span className={styles.detailTime}>TIMESTAMP: {new Date(selected.timestamp).toLocaleString()}</span>
              </div>
              <button className={styles.rerunBtn} onClick={() => handleRerun(selected.query)} title="Rerun this diagnostic session">
                <Play size={10} />
                <span>RERUN QUERY</span>
              </button>
            </div>

            <div className={styles.metaGrid}>
              <div className={styles.metaCell}>
                <span className={styles.metaLabel}>DETECTED INTENT</span>
                <span className={styles.metaVal}>{selected.intent}</span>
              </div>
              <div className={styles.metaCell}>
                <span className={styles.metaLabel}>CLEARANCE LEVEL</span>
                <span className={styles.metaVal}>{selected.risk_level}</span>
              </div>
              <div className={styles.metaCell}>
                <span className={styles.metaLabel}>RECORD STATE</span>
                <span className="badge badge-success">STORED LOCALLY</span>
              </div>
            </div>

            {selected.result && (
              <div className={styles.sectionWrap}>
                <p className={styles.sectionLabel}>// DIAGNOSTIC SYNTHESIS &amp; OUTPUT</p>
                <div className={styles.detailResult}>
                  {selected.result}
                </div>
              </div>
            )}

            {selected.commands?.length > 0 && (
              <div className={styles.sectionWrap}>
                <p className={styles.sectionLabel}>// PROPOSED COMMANDS</p>
                <div className={styles.cmdList}>
                  {selected.commands.map((cmd, i) => {
                    const cmdText = typeof cmd === 'string' ? cmd : cmd?.command || '';
                    return (
                      <div key={i} className={styles.cmdRow}>
                        <code className={styles.cmd}>{cmdText}</code>
                        <button className={styles.copyCmdBtn} onClick={() => handleCopyCmd(cmdText, i)} title="Copy command">
                          {copiedCmd === i ? <Check size={11} color="var(--color-success)" /> : <Copy size={11} />}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className={styles.noSelect}>
            <p>Select a session from the log to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}
