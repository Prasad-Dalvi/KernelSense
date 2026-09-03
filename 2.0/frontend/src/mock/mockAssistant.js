/**
 * Mock AI Assistant responses.
 * Used when VITE_USE_MOCK_API=true
 */

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const responses = {
  slow: {
    request_id: 'mock-001',
    intent: 'SYSTEM_DIAGNOSIS',
    response:
      'I analyzed your system and found **high memory pressure** as the primary cause of slowness.\n\n**Chrome** is consuming **4.2 GB RAM** across 23 tabs. Additionally, background services are contributing to **CPU spikes averaging 78%** over the last 5 minutes.',
    tools_used: ['cpu_check', 'memory_check', 'process_list', 'storage_check'],
    recommendations: [
      'Close unnecessary Chrome tabs (currently 23 open)',
      'Restart the `update-notifier` background service',
      'Consider adding 4GB more RAM — current headroom is only 400MB',
    ],
    commands: [
      {
        id: 'cmd-001',
        command: 'sudo systemctl restart update-notifier',
        risk_level: 'MEDIUM',
        explanation:
          'Restarts the update notification service. May briefly pause update checks.',
      },
    ],
    risk_level: 'LOW',
    root_cause: {
      nodes: [
        { id: 'chrome', label: 'Chrome (23 tabs)', type: 'process' },
        { id: 'mem', label: 'High Memory Usage (87%)', type: 'symptom' },
        { id: 'swap', label: 'Swap Activity', type: 'symptom' },
        { id: 'slow', label: 'System Slowdown', type: 'impact' },
      ],
      edges: [
        { from: 'chrome', to: 'mem' },
        { from: 'mem', to: 'swap' },
        { from: 'swap', to: 'slow' },
      ],
    },
    execution_steps: [
      { tool: 'cpu_check',    label: 'CPU checked',        status: 'done' },
      { tool: 'memory_check', label: 'Memory checked',     status: 'done' },
      { tool: 'process_list', label: 'Processes scanned',  status: 'done' },
      { tool: 'storage_check',label: 'Storage checked',    status: 'done' },
    ],
  },
  wifi: {
    request_id: 'mock-002',
    intent: 'NETWORK_DIAGNOSIS',
    response:
      'Your WiFi adapter is connected but **internet access is unavailable**.\n\nThe DHCP server failed to assign an IP address. NetworkManager reported a lease failure at `09:32:11`.',
    tools_used: ['network_check', 'log_check'],
    recommendations: [
      'Restart NetworkManager to request a new DHCP lease',
      'Check if the router is assigning IPs correctly',
      'Verify DNS resolution with `nslookup google.com`',
    ],
    commands: [
      {
        id: 'cmd-002',
        command: 'sudo systemctl restart NetworkManager',
        risk_level: 'MEDIUM',
        explanation:
          'Restarts NetworkManager. This will temporarily disconnect all network interfaces for 5–10 seconds.',
      },
    ],
    risk_level: 'MEDIUM',
    root_cause: {
      nodes: [
        { id: 'dhcp', label: 'DHCP Failure', type: 'event' },
        { id: 'noip', label: 'No IP Address', type: 'symptom' },
        { id: 'noint', label: 'No Internet', type: 'impact' },
      ],
      edges: [
        { from: 'dhcp', to: 'noip' },
        { from: 'noip', to: 'noint' },
      ],
    },
    execution_steps: [
      { tool: 'network_check', label: 'Network interfaces scanned', status: 'done' },
      { tool: 'log_check',     label: 'System logs checked',        status: 'done' },
    ],
  },
  default: {
    request_id: 'mock-000',
    intent: 'GENERAL_QUERY',
    response:
      'I received your query. In production mode, this will be processed by the AI layer and answered with real system data.\n\nCurrently running in **mock mode** — connect the FastAPI backend to see live responses.',
    tools_used: [],
    recommendations: ['Set VITE_USE_MOCK_API=false and start the FastAPI backend'],
    commands: [],
    risk_level: 'LOW',
    root_cause: null,
    execution_steps: [],
  },
};

export async function getMockAssistantResponse(query) {
  await delay(1800); // simulate AI thinking time
  const q = query.toLowerCase();
  if (q.includes('slow') || q.includes('memory') || q.includes('cpu')) return responses.slow;
  if (q.includes('wifi') || q.includes('network') || q.includes('internet') || q.includes('connect'))
    return responses.wifi;
  return { ...responses.default, response: responses.default.response, request_id: `mock-${Date.now()}` };
}

export function getMockHistory() {
  return [
    {
      id: 'h-001',
      query: 'Why is my laptop slow?',
      timestamp: '2026-08-18T09:42:00Z',
      intent: 'SYSTEM_DIAGNOSIS',
      commands: ['sudo systemctl restart update-notifier'],
      result: 'High memory usage identified. Chrome using 4.2GB RAM.',
      risk_level: 'LOW',
      status: 'success',
    },
    {
      id: 'h-002',
      query: 'Diagnose WiFi connection',
      timestamp: '2026-08-18T09:30:00Z',
      intent: 'NETWORK_DIAGNOSIS',
      commands: ['sudo systemctl restart NetworkManager'],
      result: 'DHCP failure detected. NetworkManager restarted.',
      risk_level: 'MEDIUM',
      status: 'success',
    },
    {
      id: 'h-003',
      query: 'Find large PDF files',
      timestamp: '2026-08-18T09:12:00Z',
      intent: 'FILE_SEARCH',
      commands: [],
      result: 'Found 14 PDF files larger than 50MB in /home/user/Documents.',
      risk_level: 'LOW',
      status: 'success',
    },
    {
      id: 'h-004',
      query: 'What services are failing?',
      timestamp: '2026-08-18T08:55:00Z',
      intent: 'SERVICE_CHECK',
      commands: [],
      result: '2 failed services found: bluetooth.service, cups.service',
      risk_level: 'LOW',
      status: 'success',
    },
  ];
}
