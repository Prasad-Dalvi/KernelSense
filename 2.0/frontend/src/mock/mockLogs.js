export function getMockLogs() {
  return [
    { id: 'l-001', timestamp: '2026-08-18T09:32:11Z', service: 'NetworkManager', message: 'DHCP request failed on wlan0 — no lease obtained after 3 retries.', severity: 'warning', pid: 2908 },
    { id: 'l-002', timestamp: '2026-08-18T09:28:44Z', service: 'kernel',         message: 'Out of memory: Kill process 7821 (postgres) score 421 or sacrifice child', severity: 'critical', pid: null },
    { id: 'l-003', timestamp: '2026-08-18T09:12:07Z', service: 'systemd',        message: 'update-notifier.service: Main process exited, code=killed, status=9/KILL', severity: 'warning', pid: 6643 },
    { id: 'l-004', timestamp: '2026-08-18T08:55:30Z', service: 'bluetooth',      message: 'bluetooth.service: Failed with result exit-code.', severity: 'critical', pid: null },
    { id: 'l-005', timestamp: '2026-08-18T08:40:00Z', service: 'systemd',        message: 'Reached target graphical.target — system started successfully.', severity: 'info', pid: 1 },
    { id: 'l-006', timestamp: '2026-08-18T08:38:12Z', service: 'sshd',           message: 'Server listening on 0.0.0.0 port 22.', severity: 'info', pid: 1201 },
    { id: 'l-007', timestamp: '2026-08-18T08:35:44Z', service: 'cups',           message: 'Scheduler shutdown normally.', severity: 'info', pid: 9102 },
    { id: 'l-008', timestamp: '2026-08-18T08:30:00Z', service: 'NetworkManager', message: 'wlan0: connected to HomeNetwork-5G', severity: 'info', pid: 2908 },
    { id: 'l-009', timestamp: '2026-08-18T08:25:15Z', service: 'cron',           message: 'pam_unix(cron:session): session opened for user root', severity: 'info', pid: 3301 },
    { id: 'l-010', timestamp: '2026-08-18T07:55:00Z', service: 'kernel',         message: 'EXT4-fs (sda1): re-mounted. Opts: errors=remount-ro', severity: 'info', pid: null },
    { id: 'l-011', timestamp: '2026-08-18T07:50:00Z', service: 'ufw',            message: 'UFW BLOCK: IN=wlan0 OUT= SRC=192.168.1.200 DST=192.168.1.105 PROTO=TCP DPT=22', severity: 'warning', pid: null },
    { id: 'l-012', timestamp: '2026-08-18T07:40:00Z', service: 'apt',            message: 'Packages updated: linux-headers-6.5.0, libssl3', severity: 'info', pid: null },
  ];
}
