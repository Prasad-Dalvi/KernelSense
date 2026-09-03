/**
 * Mock system statistics.
 */

function generateHistory(base, variance, count = 20) {
  return Array.from({ length: count }, (_, i) => ({
    time: `${String(9 + Math.floor(i / 4)).padStart(2, '0')}:${String((i % 4) * 15).padStart(2, '0')}`,
    value: Math.max(0, Math.min(100, base + (Math.random() - 0.5) * variance * 2)),
  }));
}

export function getMockSystem() {
  return {
    cpu: {
      usage: 42,
      cores: 8,
      load_avg: [1.32, 1.87, 2.10],
      temperature: 58,
      history: generateHistory(42, 20),
    },
    memory: {
      usage: 67,
      total_gb: 16,
      used_gb: 10.7,
      free_gb: 5.3,
      swap_used: 23,
      history: generateHistory(67, 15),
    },
    storage: {
      usage: 71,
      total_gb: 512,
      used_gb: 363,
      available_gb: 149,
      largest_dirs: [
        { path: '/home/user/.local/share', size_gb: 48.2 },
        { path: '/var/log',                size_gb: 12.4 },
        { path: '/usr/lib',                size_gb: 8.9  },
        { path: '/home/user/Downloads',    size_gb: 31.1 },
        { path: '/home/user/Documents',    size_gb: 7.3  },
      ],
      large_files: [
        { path: '/home/user/Downloads/ubuntu.iso', size_gb: 4.7 },
        { path: '/home/user/.local/share/Steam/steamapps/common/game.iso', size_gb: 12.3 },
        { path: '/var/log/syslog.1', size_gb: 1.1 },
      ],
      recommendations: [
        'Remove /home/user/Downloads/ubuntu.iso (4.7 GB, 8 months old)',
        'Clear /var/log — 12.4 GB of old logs',
        'Run `sudo apt autoremove` to free ~800 MB',
      ],
      history: generateHistory(71, 3),
    },
    network: {
      interfaces: [
        { name: 'wlan0', status: 'up', ip: '192.168.1.105', type: 'wifi' },
        { name: 'lo',    status: 'up', ip: '127.0.0.1',     type: 'loopback' },
      ],
      internet: true,
      download_mbps: 94.2,
      upload_mbps: 42.1,
    },
    health: {
      score: 87,
      categories: [
        { name: 'Performance', score: 91, status: 'good',            explanation: 'CPU usage is within normal range.', recommendation: 'Monitor during peak hours.' },
        { name: 'Memory',      score: 78, status: 'needs_attention', explanation: 'Memory usage consistently above 65%.', recommendation: 'Close unused applications or add RAM.' },
        { name: 'Storage',     score: 85, status: 'good',            explanation: '71% storage used — approaching threshold.', recommendation: 'Clear downloads folder.' },
        { name: 'Network',     score: 94, status: 'good',            explanation: 'Network is stable with no packet loss.', recommendation: 'No action needed.' },
        { name: 'Security',    score: 88, status: 'good',            explanation: 'Firewall active. No open suspicious ports.', recommendation: 'Keep system packages updated.' },
      ],
    },
  };
}

export function getMockRecentEvents() {
  return [
    { id: 'e-001', timestamp: '09:32:11', title: 'DHCP request failed', severity: 'warning', source: 'NetworkManager' },
    { id: 'e-002', timestamp: '09:28:44', title: 'High memory usage detected (87%)', severity: 'warning', source: 'kernel' },
    { id: 'e-003', timestamp: '09:12:07', title: 'update-notifier restarted', severity: 'info', source: 'systemd' },
    { id: 'e-004', timestamp: '08:55:30', title: 'Bluetooth service failed', severity: 'critical', source: 'bluetooth' },
    { id: 'e-005', timestamp: '08:40:00', title: 'System boot completed', severity: 'info', source: 'systemd' },
  ];
}
