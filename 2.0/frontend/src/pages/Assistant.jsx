import React, { useRef, useEffect, useState } from 'react';
import { RotateCcw, Copy, Check, Sparkles, Terminal, Bot, Send, Zap, Mic, MicOff } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { useAssistant } from '../hooks/useAssistant';
import { runReadOnlyTerminal, transcribeVoice } from '../api/assistantApi';
import { sound } from '../utils/soundEffects';
import CommandApproval from '../components/CommandApproval';
import ToolProgress from '../components/ToolProgress';
import RootCauseTree from '../components/RootCauseTree';
import styles from './Assistant.module.css';

const PROVIDER_MODELS = {
  gemini: [
    { value: '', label: 'Backend default' },
    { value: 'gemini-3.1-flash-lite-preview', label: 'Gemini 3.1 Flash-Lite Preview' },
    { value: 'gemini-flash-lite-latest', label: 'Gemini Flash-Lite' },
    { value: 'gemini-flash-latest', label: 'Gemini Flash' },
  ],
  grok: [
    { value: '', label: 'Backend default' },
    { value: 'grok-4.7', label: 'Grok 4.7' },
    { value: 'grok-4.6', label: 'Grok 4.6' },
    { value: 'grok-4.5', label: 'Grok 4.5' },
    { value: 'grok-4.3', label: 'Grok 4.3' },
    { value: 'grok-4.20-0309-reasoning', label: 'Grok 4.20 Reasoning' },
    { value: 'grok-4.20-0309-non-reasoning', label: 'Grok 4.20 Non-Reasoning' },
  ],
};

function readSessionPreference(key, fallback = '') {
  try {
    return window.sessionStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function writeSessionPreference(key, value) {
  try {
    window.sessionStorage.setItem(key, value);
  } catch {
    // The preference remains active for the current page even if storage is unavailable.
  }
}

export default function Assistant() {
  const { messages, loading, error, sendMessage, handleApprove, handleReject, clearMessages } = useAssistant();
  const [input, setInput] = useState('');
  const [provider, setProvider] = useState(() => {
    const saved = readSessionPreference('kernelsense.provider', 'gemini');
    return saved === 'grok' ? 'grok' : 'gemini';
  });
  const [selectedModels, setSelectedModels] = useState(() => ({
    gemini: readSessionPreference('kernelsense.model.gemini'),
    grok: readSessionPreference('kernelsense.model.grok'),
  }));
  const model = selectedModels[provider];
  const [apiKeys, setApiKeys] = useState({ gemini: '', grok: '' });
  const apiKey = apiKeys[provider];
  const [terminalOpen, setTerminalOpen] = useState(false);
  const [terminalCommand, setTerminalCommand] = useState('');
  const [terminalCwd, setTerminalCwd] = useState('');
  const [terminalOutput, setTerminalOutput] = useState('');
  const [terminalBusy, setTerminalBusy] = useState(false);
  const [terminalError, setTerminalError] = useState('');
  const [searchParams, setSearchParams] = useSearchParams();
  const bottomRef = useRef(null);
  const autoSubmittedRef = useRef(false);
  const inputRef = useRef(null);
  const audioGraphRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const baseInputRef = useRef('');
  const recordingTimerRef = useRef(null);
  const voiceBusyRef = useRef(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [speechError, setSpeechError] = useState(null);
  const voiceSupported = typeof window !== 'undefined'
    && Boolean(
      (window.AudioContext || window.webkitAudioContext)?.prototype?.createScriptProcessor
      && navigator.mediaDevices?.getUserMedia
    );

  useEffect(() => {
    const q = searchParams.get('q');
    if (q && !autoSubmittedRef.current) {
      autoSubmittedRef.current = true;
      setSearchParams({}, { replace: true });
      sound.send();
      sendMessage(q, { provider, model, apiKey });
    }
  }, [searchParams, setSearchParams, sendMessage, provider, model, apiKey]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => () => {
    if (recordingTimerRef.current) {
      window.clearTimeout(recordingTimerRef.current);
    }
    const graph = audioGraphRef.current;
    if (graph) {
      graph.processor.onaudioprocess = null;
      graph.source.disconnect();
      graph.processor.disconnect();
      graph.mute.disconnect();
      graph.context.close();
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  const submit = (query) => {
    const q = query ?? input;
    if (!q.trim() || loading || isRecording || isTranscribing) return;
    sound.send();
    setInput('');
    sendMessage(q, { provider, model, apiKey });
  };

  const runTerminal = async (event) => {
    event.preventDefault();
    const command = terminalCommand.trim();
    if (!command || terminalBusy) return;

    setTerminalCommand('');
    setTerminalBusy(true);
    setTerminalError('');
    setTerminalOutput((output) => `${output}${output ? '\n' : ''}${terminalCwd || 'local'}> ${command}\n`);
    try {
      const result = await runReadOnlyTerminal(command, terminalCwd);
      setTerminalCwd(result.cwd);
      setTerminalOutput((output) => `${output}${result.output || '(no output)'}\n`.slice(-16000));
      if (!result.success) setTerminalError('The command returned an error.');
    } catch (requestError) {
      setTerminalError(requestError?.message ?? 'The read-only terminal request failed.');
    } finally {
      setTerminalBusy(false);
    }
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

  const finishVoiceRecording = async () => {
    const graph = audioGraphRef.current;
    if (!graph) return;
    if (recordingTimerRef.current) {
      window.clearTimeout(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }

    graph.processor.onaudioprocess = null;
    graph.source.disconnect();
    graph.processor.disconnect();
    graph.mute.disconnect();
    audioGraphRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setIsRecording(false);
    setIsTranscribing(true);
    setSpeechError(null);
    try {
      await graph.context.close();
      const wav = convertPcmChunksToWav(audioChunksRef.current, graph.context.sampleRate);
      audioChunksRef.current = [];
      const transcript = (await transcribeVoice(wav)).trim();
      if (!transcript) throw new Error('No speech was recognized. Try again.');
      const prefix = baseInputRef.current;
      setInput(`${prefix}${prefix ? ' ' : ''}${transcript}`);
    } catch (error) {
      setSpeechError(error?.message ?? 'Could not transcribe the recording.');
    } finally {
      voiceBusyRef.current = false;
      setIsTranscribing(false);
    }
  };

  const toggleVoiceInput = async () => {
    if (isRecording) {
      await finishVoiceRecording();
      return;
    }
    if (voiceBusyRef.current) return;
    if (!voiceSupported) {
      setSpeechError('Audio recording is not supported by this browser.');
      return;
    }

    voiceBusyRef.current = true;
    baseInputRef.current = input.trimEnd();
    let context;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      context = new AudioContextClass();
      await context.resume();
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: { ideal: 1 },
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;
      audioChunksRef.current = [];
      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 2, 1);
      const mute = context.createGain();
      mute.gain.value = 0;
      processor.onaudioprocess = (event) => {
        const input = event.inputBuffer;
        const samples = new Float32Array(input.length);
        const channels = Array.from(
          { length: input.numberOfChannels },
          (_, index) => input.getChannelData(index)
        );
        for (let frame = 0; frame < input.length; frame += 1) {
          let sample = 0;
          for (const channel of channels) {
            sample += channel[frame];
          }
          samples[frame] = sample / channels.length;
        }
        audioChunksRef.current.push(samples);
      };
      source.connect(processor);
      processor.connect(mute);
      mute.connect(context.destination);
      audioGraphRef.current = { context, source, processor, mute };
      setSpeechError(null);
      setIsRecording(true);
      recordingTimerRef.current = window.setTimeout(finishVoiceRecording, 60000);
    } catch (error) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (context && context.state !== 'closed') await context.close();
      voiceBusyRef.current = false;
      const message = error?.name === 'NotAllowedError'
        ? 'Microphone access was denied. Allow microphone access in your browser settings.'
        : error?.name === 'NotFoundError'
        ? 'No microphone was found.'
        : error?.message ?? 'Could not start voice input.';
      setSpeechError(message);
    }
  };

  return (
    <div className={styles.page}>
      {/* ── Chat Feed Stream ── */}
      <div className={styles.chatWindow}>
        {messages.length === 0 ? (
          <WelcomeHero />
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
            <span>SYSTEM ASSISTANT</span>
          </div>
          {messages.length > 0 && (
            <button className={styles.clearBtn} onClick={handleClear} title="Clear conversation history">
              <RotateCcw size={11} />
              <span>Clear History</span>
            </button>
          )}
          <button
            className={styles.terminalToggle}
            onClick={() => setTerminalOpen((open) => !open)}
            aria-expanded={terminalOpen}
            type="button"
          >
            <Terminal size={12} />
            <span>{terminalOpen ? 'Hide Terminal' : 'Open Terminal'}</span>
          </button>
        </div>

        <div className={styles.providerControls}>
          <label className={styles.providerField}>
            <span>Ask agent with</span>
            <select
              value={provider}
              onChange={(e) => {
                setProvider(e.target.value);
                writeSessionPreference('kernelsense.provider', e.target.value);
              }}
              disabled={loading}
            >
              <option value="gemini">Gemini</option>
              <option value="grok">Grok (xAI)</option>
            </select>
          </label>
          <label className={styles.providerField}>
            <span>Model</span>
            <select
              value={model}
              onChange={(e) => {
                setSelectedModels((models) => ({ ...models, [provider]: e.target.value }));
                writeSessionPreference(`kernelsense.model.${provider}`, e.target.value);
              }}
              disabled={loading}
            >
              {PROVIDER_MODELS[provider].map((option) => (
                <option key={option.value || 'backend-default'} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label className={styles.providerField}>
            <span>{provider === 'gemini' ? 'Gemini' : 'Grok'} API key</span>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKeys((keys) => ({ ...keys, [provider]: e.target.value }))}
              placeholder="Optional if configured in backend .env"
              autoComplete="off"
              spellCheck="false"
              disabled={loading}
            />
          </label>
          <span className={styles.keyPrivacyNote}>Sent only to this provider through the local backend; not saved.</span>
        </div>

        {terminalOpen && (
          <section className={styles.terminalPanel} aria-label="Read-only local terminal">
            <div className={styles.terminalHeader}>
              <span>WINDOWS LOCAL TERMINAL · READ ONLY</span>
              <span>{terminalCwd || 'Working directory loads on first command'}</span>
            </div>
            <pre className={styles.terminalOutput} aria-live="polite">
              {terminalOutput || 'Type help to see the supported commands.'}
            </pre>
            {terminalError && <p className={styles.terminalError} role="alert">{terminalError}</p>}
            <form className={styles.terminalForm} onSubmit={runTerminal}>
              <span className={styles.terminalPrompt}>{terminalCwd || 'local'}&gt;</span>
              <input
                value={terminalCommand}
                onChange={(event) => setTerminalCommand(event.target.value)}
                placeholder='help, pwd, cd "folder", dir "folder" --limit 5, whoami...'
                aria-label="Read-only terminal command"
                autoComplete="off"
                spellCheck="false"
                disabled={terminalBusy}
              />
              <button type="submit" disabled={terminalBusy || !terminalCommand.trim()}>
                {terminalBusy ? 'Running…' : 'Run'}
              </button>
            </form>
            <p className={styles.terminalNote}>
              Only directory listing/navigation and system information are allowed; no arbitrary shell commands or file changes.
            </p>
          </section>
        )}

        <div className={styles.inputWrap}>
          <textarea
            id="assistant-input"
            ref={inputRef}
            className={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
            placeholder="Ask about your computer or describe an issue..."
            rows={1}
            disabled={loading || isRecording || isTranscribing}
          />
          <button
            type="button"
            className={`${styles.voiceButton} ${isRecording ? styles.voiceButtonActive : ''}`}
            onClick={toggleVoiceInput}
            disabled={loading || isTranscribing || !voiceSupported}
            aria-label={isRecording ? 'Stop voice recording' : 'Start voice recording'}
            aria-pressed={isRecording}
            title={!voiceSupported ? 'Audio recording is not supported by this browser' : isRecording ? 'Stop recording and transcribe' : 'Record a voice prompt'}
          >
            {isRecording ? <MicOff size={15} /> : <Mic size={15} />}
          </button>
          <button
            id="assistant-send"
            className={styles.sendButton}
            onClick={() => submit()}
            disabled={loading || isRecording || isTranscribing || !input.trim()}
          >
            {loading ? <span className="spin">◌</span> : <Send size={15} />}
          </button>
        </div>

        <div className={styles.inputFooter}>
          <span className={styles.hintKey}><kbd>Enter</kbd> to submit</span>
          <span className={styles.hintKey}><kbd>Shift + Enter</kbd> newline</span>
          <span className={styles.hintKey}><kbd>Ctrl + K</kbd> quick ops</span>
        </div>
        <p className={styles.voiceNote} role={speechError ? 'alert' : 'status'}>
          {speechError || (isRecording
            ? 'Recording… click the microphone again to stop. Recording stops automatically after 60 seconds.'
            : isTranscribing
            ? 'Transcribing locally with Whisper. First use may take longer while the model downloads…'
            : voiceSupported
            ? 'High-accuracy Whisper transcription runs locally. Audio stays in memory and is never sent to Gemini/Grok.'
            : 'Audio recording is not supported by this browser.')}
        </p>
      </div>
    </div>
  );
}

function convertPcmChunksToWav(chunks, sourceRate) {
  const totalFrames = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const inputFrames = Math.min(totalFrames, Math.floor(sourceRate * 60));
  if (!inputFrames) throw new Error('No audio was recorded. Try again.');

  const input = new Float32Array(inputFrames);
  let inputOffset = 0;
  for (const chunk of chunks) {
    const frames = Math.min(chunk.length, inputFrames - inputOffset);
    input.set(chunk.subarray(0, frames), inputOffset);
    inputOffset += frames;
    if (inputOffset === inputFrames) break;
  }

  const targetRate = 16000;
  const ratio = sourceRate / targetRate;
  const outputFrames = Math.floor(inputFrames / ratio);
  const wav = new ArrayBuffer(44 + outputFrames * 2);
  const view = new DataView(wav);
  const writeString = (offset, value) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };
  writeString(0, 'RIFF');
  view.setUint32(4, wav.byteLength - 8, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, targetRate, true);
  view.setUint32(28, targetRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, outputFrames * 2, true);
  for (let index = 0; index < outputFrames; index += 1) {
    const sourcePosition = index * ratio;
    const lower = Math.floor(sourcePosition);
    const upper = Math.min(lower + 1, inputFrames - 1);
    const fraction = sourcePosition - lower;
    const sample = Math.max(-1, Math.min(1, input[lower] * (1 - fraction) + input[upper] * fraction));
    view.setInt16(44 + index * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
  }
  return new Blob([wav], { type: 'audio/wav' });
}

// ─── Welcome Hero Nexus with 3D Neural Core ──────────────────────────────

function WelcomeHero() {
  return (
    <div className={styles.welcomeContainer}>
      <div className={`${styles.welcomeHeroCard} glass-card`}>
        <div className={styles.welcomeHeroLeft}>
          <div className={styles.modelBadge}>
            <Sparkles size={13} />
            <span>KERNELSENSE ASSISTANT</span>
          </div>

          <h2 className={styles.welcomeTitle}>
            How can I help with <span className="grad-text">your computer</span>?
          </h2>

          <p className={styles.welcomeDesc}>
            Ask about current system metrics, processes, storage, network, or a proposed action.
          </p>
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
