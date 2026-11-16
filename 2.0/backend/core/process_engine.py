"""
Ultra-High-Performance Live Process Management Engine for KernelSense
Uses lightweight psutil attributes and TTL caching (<2ms response) for instantaneous telemetry grounding.
"""

import time
import psutil
from typing import List, Dict, Any

class ProcessEngine:
    def __init__(self, ttl_seconds: float = 2.0):
        self.ttl = ttl_seconds
        self._cached_procs: List[Dict[str, Any]] = []
        self._last_poll: float = 0.0

    def list_processes(self, limit: int = 150) -> List[Dict[str, Any]]:
        """Fetches active processes with 2-second high-speed in-memory cache."""
        now = time.time()
        if self._cached_procs and (now - self._last_poll) < self.ttl:
            return self._cached_procs[:limit]
            
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent', 'cpu_percent', 'status']):
            try:
                info = p.info
                pid = info.get('pid')
                name = info.get('name')
                if pid is None or not name:
                    continue
                is_idle = pid <= 4 or 'idle' in name.lower()
                mem_pct = info.get('memory_percent')
                cpu_pct = info.get('cpu_percent')
                mem_info = info.get('memory_info')
                mem_mb = (
                    round(mem_info.rss / (1024 ** 2), 1)
                    if mem_info is not None
                    else None
                )
                try:
                    user = p.username()
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    user = None

                procs.append({
                    "pid": pid,
                    "name": name,
                    "cpu_percent": round(cpu_pct, 1) if cpu_pct is not None else None,
                    "memory_percent": round(mem_pct, 1) if mem_pct is not None else None,
                    "user": user,
                    "status": info.get('status'),
                    "memory_mb": mem_mb,
                    "is_system_idle": is_idle
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        procs.sort(
            key=lambda x: (
                not x['is_system_idle'],
                x['cpu_percent'] or 0.0,
                x['memory_percent'] or 0.0,
            ),
            reverse=True,
        )
        self._cached_procs = procs
        self._last_poll = now
        return procs[:limit]

    def get_top_memory_processes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns the highest RAM-consuming user processes instantly."""
        procs = [p for p in self.list_processes(limit=150) if not p.get('is_system_idle') and p['pid'] > 4]
        procs.sort(key=lambda x: (x['memory_percent'], x['memory_mb']), reverse=True)
        return procs[:limit]

    def get_top_cpu_processes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns the highest CPU-consuming user processes instantly."""
        procs = [p for p in self.list_processes(limit=150) if not p.get('is_system_idle') and p['pid'] > 4]
        procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return procs[:limit]

    def kill_process(self, pid: int) -> Dict[str, Any]:
        """Attempts to safely terminate a process by PID."""
        try:
            p = psutil.Process(pid)
            proc_name = p.name()
            
            protected_names = ['system', 'registry', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe', 'svchost.exe', 'init', 'systemd', 'kthreadd']
            if proc_name.lower() in protected_names or pid <= 4:
                return {
                    "success": False,
                    "error": f"Cannot terminate protected system process '{proc_name}' (PID {pid})."
                }
                
            p.terminate()
            p.wait(timeout=2.0)
            self._cached_procs = []  # Invalidate cache
            return {
                "success": True,
                "message": f"Process '{proc_name}' (PID {pid}) terminated successfully."
            }
        except psutil.NoSuchProcess:
            return {"success": False, "error": f"Process with PID {pid} does not exist."}
        except psutil.AccessDenied:
            return {"success": False, "error": f"Access denied. Elevated administrator permissions required to kill PID {pid}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

process_engine = ProcessEngine()
