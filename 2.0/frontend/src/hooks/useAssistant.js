import { useState, useCallback, useRef } from 'react';
import { askAssistant, approveCommand, rejectCommand } from '../api/assistantApi';

export function useAssistant() {
  const [messages, setMessages]   = useState([]);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  // Note: abort controller wiring reserved for when streaming AI responses are added
  const _abortRef = useRef(null);

  const sendMessage = useCallback(async (query, options = {}) => {
    if (!query.trim()) return;

    // Add user message immediately
    const userMsg = { id: Date.now(), role: 'user', content: query, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    // Add a placeholder AI message with loading state
    const aiPlaceholderId = Date.now() + 1;
    setMessages((prev) => [
      ...prev,
      { id: aiPlaceholderId, role: 'assistant', loading: true, timestamp: new Date().toISOString() },
    ]);

    try {
      const response = await askAssistant(query, options);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiPlaceholderId
            ? { ...m, loading: false, ...response }
            : m
        )
      );
    } catch (err) {
      setError(err?.message ?? 'Failed to reach KernelSense backend.');
      setMessages((prev) => prev.filter((m) => m.id !== aiPlaceholderId));
    } finally {
      setLoading(false);
    }
  }, []);

  const handleApprove = useCallback(async (commandId, requestId) => {
    try {
      const result = await approveCommand(commandId, requestId);
      setMessages((prev) =>
        prev.map((m) => {
          if (!m.commands) return m;
          return {
            ...m,
            commands: m.commands.map((c) =>
              c.id === commandId ? { ...c, executed: true, result } : c
            ),
          };
        })
      );
    } catch (err) {
      setError(err?.message ?? 'Command execution failed.');
    }
  }, []);

  const handleReject = useCallback(async (commandId, requestId) => {
    try {
      await rejectCommand(commandId, requestId);
      setMessages((prev) =>
        prev.map((m) => {
          if (!m.commands) return m;
          return {
            ...m,
            commands: m.commands.map((c) =>
              c.id === commandId ? { ...c, rejected: true } : c
            ),
          };
        })
      );
    // Intentionally silent — user cancelled, nothing to report
    // eslint-disable-next-line no-unused-vars
    } catch (_err) {}
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, handleApprove, handleReject, clearMessages };
}
