export function getMockProcesses() {
  return [
    { pid: 2301, name: 'chrome',             cpu_percent: 18.2, memory_percent: 26.3, memory_mb: 4198, user: 'user',   status: 'running' },
    { pid: 1872, name: 'Xorg',               cpu_percent: 8.1,  memory_percent: 4.2,  memory_mb: 672,  user: 'root',   status: 'running' },
    { pid: 3412, name: 'code',               cpu_percent: 6.7,  memory_percent: 7.8,  memory_mb: 1248, user: 'user',   status: 'running' },
    { pid: 4201, name: 'gnome-shell',        cpu_percent: 4.3,  memory_percent: 3.1,  memory_mb: 496,  user: 'user',   status: 'running' },
    { pid: 5510, name: 'dockerd',            cpu_percent: 3.9,  memory_percent: 2.4,  memory_mb: 384,  user: 'root',   status: 'running' },
    { pid: 1023, name: 'systemd',            cpu_percent: 0.5,  memory_percent: 0.3,  memory_mb: 48,   user: 'root',   status: 'running' },
    { pid: 2908, name: 'NetworkManager',     cpu_percent: 0.3,  memory_percent: 0.5,  memory_mb: 80,   user: 'root',   status: 'running' },
    { pid: 7821, name: 'postgres',           cpu_percent: 2.1,  memory_percent: 1.8,  memory_mb: 288,  user: 'postgres',status: 'running' },
    { pid: 6643, name: 'update-notifier',    cpu_percent: 7.8,  memory_percent: 1.1,  memory_mb: 176,  user: 'root',   status: 'running' },
    { pid: 8890, name: 'npm',                cpu_percent: 1.4,  memory_percent: 0.9,  memory_mb: 144,  user: 'user',   status: 'running' },
    { pid: 9001, name: 'pulseaudio',         cpu_percent: 0.2,  memory_percent: 0.4,  memory_mb: 64,   user: 'user',   status: 'running' },
    { pid: 9102, name: 'cups',               cpu_percent: 0.0,  memory_percent: 0.2,  memory_mb: 32,   user: 'root',   status: 'sleeping' },
    { pid: 4312, name: 'bluetooth',          cpu_percent: 0.0,  memory_percent: 0.1,  memory_mb: 16,   user: 'root',   status: 'stopped' },
  ];
}
