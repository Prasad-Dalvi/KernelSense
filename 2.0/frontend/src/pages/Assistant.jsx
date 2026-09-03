import React, { useRef, useEffect, useState } from 'react';
import { RotateCcw, Copy, Check, Sparkles, Terminal, Bot, Send, Zap, ChevronRight } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { useAssistant } from '../hooks/useAssistant';
import { sound } from '../utils/soundEffects';
import CommandApproval from '../components/CommandApproval';
import ToolProgress from '../components/ToolProgress';
import RootCauseTree from '../components/RootCauseTree';
import neuralCoreImg from '../assets/neural_core.jpg';
import styles from './Assistant.module.css';

const SUGGESTED = [
  { key: '1', text: 'Why is my laptop slow?', tag: 'PERF' },
  { key: '2', text: 'Diagnose WiFi connection issues', tag: 'NET' },
  { key: '3', text: 'Show me high memory processes', tag: 'MEM' },
  { key: '4', text: 'What services are failing?', tag: 'SYSTEMD' },
  { key: '5', text: 'Find large files on my system', tag: 'DISK' },
];

export default function Assistant() {
  const { messages, loading, error, sendMessage, handleApprove, handleReject, clearMessages } = useAssistant();
  const [input, setInput] = useState('');
  const [searchParams, setSearchParams] = useSearchParams();
  const bottomRef = useRef(null);
  const autoSubmittedRef = useRef(false);
  const inputRef = useRef(null);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q && !autoSubmittedRef.current) {
      autoSubmittedRef.current = true;
      setSearchParams({}, { replace: true });
      sound.send();
      sendMessage(q);
    }
  }, [searchParams, setSearchParams, sendMessage]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const submit = (query) => {
    const q = query ?? input;
    if (!q.trim() || loading) return;
    sound.send();
    setInput('');
    sendMessage(q);
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleClear = () => {
    sound.click();
    clearMessages();
  };

  return (
    <div className={styles.page}>
      {/* ── Chat Feed Stream ── */}
      <div className={styles.chatWindow}>
        {messages.length === 0 ? (
          <WelcomeHero onSuggest={submit} />
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              onApprove={(cmdId, reqId) => {
                sound.approve();
                handleApprove(cmdId, reqId);
              }}
              onReject={(cmdId, reqId) => {
                sound.click();
                handleReject(cmdId, reqId);
              }}
            />
          ))
        )}

        {loading && (
          <div className={`${styles.bubble} ${styles.aiBubble} fade-in`}>
            <div className={styles.bubbleHeader}>
              <div className={styles.aiAvatarPill}>
                <Sparkles size={13} className={styles.sparkleIcon} />
                <span>Neural Reasoning Engine</span>
              </div>
              <span className={styles.pulseIndicator}>
                <span className={styles.livePulse} /> SYNTHESIZING
              </span>
            </div>
            <div className={styles.aiContent}>
              <ToolProgress analyzing />
            </div>
          </div>
        )}

        {error && (
          <div className={styles.errorBanner}>
            <span>⚠ ERROR: {error}</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Modern Prompt Input Nexus ── */}
      <div className={`${styles.inputContainer} glass-card`}>
        <div className={styles.inputControls}>
          <div className={styles.sessionStatus}>
            <Terminal size={12} color="var(--color-cyan)" />
            <span>AI LINUX ORCHESTRATION TERMINAL</span>
          </div>
          {messages.length > 0 && (
            <button className={styles.clearBtn} onClick={handleClear} title="Clear conversation history">
              <RotateCcw size={11} />
              <span>Clear History</span>
            </button>
          )}
        </div>

        <div className={styles.inputWrap}>
          <textarea
            id="assistant-input"
            ref={inputRef}
            className={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
            placeholder="Ask anything (e.g. 'Why is memory full?', 'Inspect firewall ports', 'Clean old caches')..."
            rows={1}
            disabled={loading}
          />
          <button
            id="assistant-send"
            className={styles.sendButton}
            onClick={() => submit()}
            disabled={loading || !input.trim()}
          >
            {loading ? <span className="spin">◌</span> : <Send size={15} />}
          </button>
        </div>

        <div className={styles.inputFooter}>
          <span className={styles.hintKey}><kbd>Enter</kbd> to submit</span>
          <span className={styles.hintKey}><kbd>Shift + Enter</kbd> newline</span>
          <span className={styles.hintKey}><kbd>Ctrl + K</kbd> quick ops</span>
        </div>
      </div>
    </div>
  );
}

// ─── Welcome Hero Nexus with 3D Neural Core ──────────────────────────────

function WelcomeHero({ onSuggest }) {
  return (
    <div className={styles.welcomeContainer}>
      <div className={`${styles.welcomeHeroCard} glass-card`}>
        <div className={styles.welcomeHeroLeft}>
          <div className={styles.modelBadge}>
            <Sparkles size={13} />
            <span>KERNEL SENSE NEURAL CORE v2.0</span>
          </div>

          <h2 className={styles.welcomeTitle}>
            How can I assist your <span className="grad-text">Linux system</span> today?
          </h2>

          <p className={styles.welcomeDesc}>
            Deep kernel introspection, automated bottleneck diagnosis, root cause tree synthesis, and guarded command remediation.
          </p>
        </div>

        <div className={styles.welcomeHeroRight}>
          <img
            src={neuralCoreImg}
            alt="AI Neural Core"
            className={styles.coreOrbImg}
          />
        </div>
      </div>

      <div className={styles.quickPresetsSection}>
        <span className={styles.presetsLabel}>RECOMMENDED SYSTEM OPERATIONS:</span>
        <div className={styles.presetsGrid}>
          {SUGGESTED.map(({ key, text, tag }) => (
            <button
              key={key}
              className={`${styles.presetCard} glass-card`}
              onClick={() => {
                sound.nav();
                onSuggest(text);
              }}
            >
              <span className={styles.tagPill}>{tag}</span>
              <span className={styles.presetText}>{text}</span>
              <ChevronRight size={14} className={styles.presetArrow} />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Modern Message Bubble ───────────────────────────────────────────────

function MessageBubble({ msg, onApprove, onReject }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    sound.click();
    navigator.clipboard.writeText(msg.response || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (msg.role === 'user') {
    return (
      <div className={`${styles.bubble} ${styles.userBubble} fade-in`}>
        <div className={styles.userAvatarPill}>
          <span className={styles.userDot} />
          <span>Operator Command</span>
        </div>
        <div className={styles.userContent}>{msg.content}</div>
      </div>
    );
  }

  return (
    <div className={`${styles.bubble} ${styles.aiBubble} fade-in`}>
      <div className={styles.bubbleHeader}>
        <div className={styles.aiAvatarPill}>
          <Bot size={14} className={styles.aiIcon} />
          <span>KernelSense Assistant</span>
        </div>

        <button className={styles.copyButton} onClick={handleCopy} title="Copy response markdown">
          {copied ? <Check size={12} color="var(--color-emerald)" /> : <Copy size={12} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>

      <div className={styles.aiContent}>
        {/* Tool Execution Pipeline */}
        {msg.execution_steps?.length > 0 && (
          <ToolProgress steps={msg.execution_steps} />
        )}

        {/* Markdown Output */}
        <div className={styles.responseText}>
          <ReactMarkdown>{msg.response}</ReactMarkdown>
        </div>

        {/* Actionable Recommendations */}
        {msg.recommendations?.length > 0 && (
          <div className={`${styles.recommendations} glass-card`}>
            <div className={styles.recHeader}>
              <Zap size={13} color="var(--color-cyan)" />
              <span>RECOMMENDED ACTIONS</span>
            </div>
            <ol className={styles.recList}>
              {msg.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ol>
          </div>
        )}

        {/* Root Cause Tree Visualization */}
        {msg.root_cause && <RootCauseTree data={msg.root_cause} />}

        {/* Command Approvals */}
        {msg.commands?.map((cmd) => (
          <CommandApproval
            key={cmd.id}
            command={cmd}
            onApprove={(id) => onApprove(id, msg.request_id)}
            onReject={(id) => onReject(id, msg.request_id)}
          />
        ))}
      </div>
    </div>
  );
}
