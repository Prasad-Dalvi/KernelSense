/**
 * Assistant API — wraps POST /ask and related endpoints.
 * Never call axios directly from components.
 */
import { apiClient, isMockMode } from './client';
import { getMockAssistantResponse, getMockHistory } from '../mock/mockAssistant';

/**
 * Send a user query to the AI assistant.
 * @param {string} query
 * @returns {Promise<AssistantResponse>}
 */
export async function askAssistant(query) {
  if (isMockMode()) return getMockAssistantResponse(query);
  const { data } = await apiClient.post('/ask', { query });
  return normaliseAssistantResponse(data);
}

/**
 * Approve a proposed command.
 * @param {string} commandId
 * @param {string} requestId
 */
export async function approveCommand(commandId, requestId, command) {
  if (isMockMode()) {
    return { success: true, output: 'Command executed successfully (mock).', status: 'success' };
  }
  const payload = { command_id: commandId, request_id: requestId };
  if (command) payload.command = command;
  const { data } = await apiClient.post('/commands/approve', payload);
  return data;
}

/**
 * Reject a proposed command.
 */
export async function rejectCommand(commandId, requestId) {
  if (isMockMode()) return { success: true };
  const { data } = await apiClient.post('/commands/reject', { command_id: commandId, request_id: requestId });
  return data;
}

/**
 * Fetch conversation history.
 */
export async function fetchHistory() {
  if (isMockMode()) return getMockHistory();
  const { data } = await apiClient.get('/history');
  return Array.isArray(data) ? data : data.items ?? [];
}

// ─── Normalisers ────────────────────────────────────────────────────────────
function normaliseAssistantResponse(raw) {
  return {
    request_id:      raw.request_id      ?? raw.id ?? null,
    intent:          raw.intent          ?? 'UNKNOWN',
    response:        raw.response        ?? raw.message ?? '',
    tools_used:      raw.tools_used      ?? raw.tools ?? [],
    recommendations: raw.recommendations ?? [],
    commands:        (raw.commands ?? []).map(normaliseCommand),
    risk_level:      raw.risk_level      ?? 'LOW',
    root_cause:      raw.root_cause      ?? null,
    execution_steps: raw.execution_steps ?? [],
  };
}

function normaliseCommand(cmd) {
  return {
    id:          cmd.id          ?? cmd.command_id ?? Math.random().toString(36).slice(2),
    command:     cmd.command     ?? cmd.cmd ?? '',
    risk_level:  cmd.risk_level  ?? 'LOW',
    explanation: cmd.explanation ?? cmd.description ?? '',
  };
}
