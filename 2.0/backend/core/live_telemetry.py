"""
Live Telemetry & System Monitoring Engine for KernelSense
Interacts directly with OS hardware via psutil, socket, and system calls to retrieve:
- CPU core utilization and load averages
- Memory and Swap usage statistics
- Disk partitions, space, and I/O rates
- Network interfaces and active connectivity
- Overall algorithmic Health Score
"""

import time
import os
import socket
import psutil
import numpy as np
import platform
import datetime
from typing import Dict, Any, List
from collections import deque

class TelemetryCollector:
    def __init__(self, history_len: int = 30):
        self.history_len = history_len
        self.cpu_history = deque(maxlen=history_len)
        self.memory_history = deque(maxlen=history_len)
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_disk_time = time.time()
        cpu_stats = psutil.cpu_stats()
        self.last_context_switches = cpu_stats.ctx_switches if cpu_stats else 0
        self.last_context_switch_time = time.monotonic()
        
        self.last_internet_check = 0.0
        self.cached_internet_available = True

    def get_cpu_stats(self) -> Dict[str, Any]:
        """Returns live CPU usage, per-core breakdown, load average and history."""
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        overall = float(np.mean(per_core)) if per_core else float(psutil.cpu_percent(interval=None))
        self.cpu_history.append(round(overall, 1))
        
        # Windows does not expose a load average through psutil or os.getloadavg.
        try:
            load_avg = [round(x, 2) for x in os.getloadavg()]
        except (AttributeError, OSError):
            load_avg = None
            
        return {
            "cpu_usage": round(overall, 1),
            "cpu_count": psutil.cpu_count(logical=True) or 1,
            "physical_cores": psutil.cpu_count(logical=False) or 1,
            "load_avg": load_avg,
            "temperature": None,
            "per_core": [round(c, 1) for c in per_core],
            "history": [{"time": f"{i}", "value": val} for i, val in enumerate(self.cpu_history)]
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """Returns RAM and Swap memory usage."""
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.memory_history.append(round(vm.percent, 1))
        
        return {
            "memory_percent": round(vm.percent, 1),
            "total_gb": round(vm.total / (1024 ** 3), 2),
            "used_gb": round(vm.used / (1024 ** 3), 2),
            "free_gb": round(vm.available / (1024 ** 3), 2),
            "swap_percent": round(swap.percent, 1),
            "swap_total_gb": round(swap.total / (1024 ** 3), 2),
            "swap_used_gb": round(swap.used / (1024 ** 3), 2),
            "history": [{"time": f"{i}", "value": val} for i, val in enumerate(self.memory_history)]
        }

    def get_storage_stats(self) -> Dict[str, Any]:
        """Returns disk usage, partitions, and largest folders."""
        partitions = psutil.disk_partitions(all=False)
        total_bytes = 0
        used_bytes = 0
        free_bytes = 0
        
        partition_details = []
        for p in partitions:
            try:
                usage = psutil.disk_usage(p.mountpoint)
                total_bytes += usage.total
                used_bytes += usage.used
                free_bytes += usage.free
                partition_details.append({
                    "mountpoint": p.mountpoint,
                    "device": p.device,
                    "fstype": p.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "percent": round(usage.percent, 1)
                })
            except (PermissionError, OSError):
                continue
                
        total_gb = round(total_bytes / (1024 ** 3), 2) if total_bytes > 0 else None
        used_gb = round(used_bytes / (1024 ** 3), 2) if total_bytes > 0 else None
        avail_gb = round(free_bytes / (1024 ** 3), 2) if total_bytes > 0 else None
        usage_pct = round((used_bytes / total_bytes * 100.0), 1) if total_bytes > 0 else None
        
        # Recommendations
        recs = []
        if usage_pct is not None and usage_pct > 85.0:
            recs.append("Detected volume usage exceeds 85%. Review large files and installed applications.")
        if usage_pct is not None and usage_pct > 92.0:
            recs.append("Detected volume usage exceeds 92%. Free space on a mounted volume.")
            
        return {
            "usage_percent": usage_pct,
            "total_gb": total_gb,
            "used_gb": used_gb,
            "available_gb": avail_gb,
            "partitions": partition_details,
            "recommendations": recs
        }

    def get_network_stats(self) -> Dict[str, Any]:
        """Returns network interfaces, speeds, and internet status."""
        now = time.time()
        dt = max(now - self.last_net_time, 0.1)
        curr_net = psutil.net_io_counters()
        
        sent_rate = (curr_net.bytes_sent - self.last_net_io.bytes_sent) / dt / (1024 * 1024)
        recv_rate = (curr_net.bytes_recv - self.last_net_io.bytes_recv) / dt / (1024 * 1024)
        
        self.last_net_io = curr_net
        self.last_net_time = now
        
        # Check active internet connectivity with cache to avoid polling latency
        now = time.time()
        if now - self.last_internet_check > 4.0:
            self.last_internet_check = now
            internet_ok = False
            try:
                with socket.create_connection(("1.1.1.1", 53), timeout=0.3) as s:
                    internet_ok = True
            except (OSError, socket.timeout):
                try:
                    with socket.create_connection(("8.8.8.8", 53), timeout=0.3) as s:
                        internet_ok = True
                except OSError:
                    internet_ok = False
            self.cached_internet_available = internet_ok
        else:
            internet_ok = self.cached_internet_available
                
        # Interfaces
        if_addrs = psutil.net_if_addrs()
        if_stats = psutil.net_if_stats()
        
        interfaces = []
        for name, addrs in if_addrs.items():
            ip_str = None
            for a in addrs:
                if a.family == socket.AF_INET:
                    ip_str = a.address
                    break
            is_up = if_stats[name].isup if name in if_stats else True
            iface_type = "wireless" if "wi-fi" in name.lower() or "wlan" in name.lower() else "ethernet"
            if "loopback" in name.lower() or "lo" == name.lower():
                iface_type = "loopback"
                
            interfaces.append({
                "name": name,
                "status": "up" if is_up else "down",
                "ip_address": ip_str,
                "type": iface_type
            })
            
        return {
            "interfaces": interfaces,
            "internet_available": internet_ok,
            "download_mbps": round(max(recv_rate * 8.0, 0.0), 2),
            "upload_mbps": round(max(sent_rate * 8.0, 0.0), 2)
        }

    def get_feature_vector_for_ml(self) -> Dict[str, float]:
        """Calculates current multivariate metric vector for ML Anomaly Detector."""
        cpu_s = self.get_cpu_stats()
        mem_s = self.get_memory_stats()
        
        # Calculate memory slope over last 5 samples
        recent_m = list(self.memory_history)[-5:]
        mem_slope = float(recent_m[-1] - recent_m[0]) / max(len(recent_m), 1) if len(recent_m) > 1 else 0.0
        
        # Disk I/O rate
        now = time.time()
        dt = max(now - self.last_disk_time, 0.1)
        curr_disk = psutil.disk_io_counters()
        if curr_disk is None or self.last_disk_io is None:
            raise RuntimeError("Disk I/O counters are unavailable on this system.")
        read_rate = (curr_disk.read_bytes - self.last_disk_io.read_bytes) / dt / (1024 * 1024)
        write_rate = (curr_disk.write_bytes - self.last_disk_io.write_bytes) / dt / (1024 * 1024)
        self.last_disk_io = curr_disk
        self.last_disk_time = now
        
        # Network rate
        net_s = self.get_network_stats()
        
        num_threads = 0
        for process in psutil.process_iter(["num_threads"]):
            try:
                num_threads += process.info.get("num_threads") or 0
            except (psutil.Error, OSError):
                continue

        cpu_stats = psutil.cpu_stats()
        context_switches = 0.0
        if cpu_stats is not None:
            context_switch_time = time.monotonic()
            elapsed = max(context_switch_time - self.last_context_switch_time, 0.001)
            context_switches = max(
                cpu_stats.ctx_switches - self.last_context_switches, 0
            ) / elapsed
            self.last_context_switches = cpu_stats.ctx_switches
            self.last_context_switch_time = context_switch_time
            
        return {
            'cpu_percent': float(cpu_s['cpu_usage']),
            'cpu_variance': float(np.var(cpu_s.get('per_core', [cpu_s['cpu_usage']]))),
            'mem_percent': float(mem_s['memory_percent']),
            'mem_slope': round(mem_slope, 3),
            'swap_percent': float(mem_s['swap_percent']),
            'disk_read_mbs': round(max(read_rate, 0.0), 2),
            'disk_write_mbs': round(max(write_rate, 0.0), 2),
            'net_sent_mbs': round(net_s['upload_mbps'] / 8.0, 2),
            'net_recv_mbs': round(net_s['download_mbps'] / 8.0, 2),
            'context_switches': float(context_switches),
            'num_threads': float(num_threads)
        }

    def get_host_info(self) -> Dict[str, Any]:
        """Returns host identity and hardware values available from the OS."""
        system = platform.system()
        release = platform.release()
        version = platform.version()
        os_name = f"{system} {release}".strip()

        if system == "Windows":
            try:
                build = int(version.rsplit(".", 1)[-1])
            except ValueError:
                build = 0
            if build >= 22000:
                os_name = "Windows 11"
            elif build >= 10240:
                os_name = "Windows 10"

        boot_time = psutil.boot_time()
        frequency = psutil.cpu_freq()
        return {
            "os_name": os_name,
            "os_release": release,
            "os_version": version,
            "host_name": platform.node(),
            "machine": platform.machine(),
            "processor": platform.processor() or None,
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "cpu_frequency_mhz": round(frequency.current, 1) if frequency else None,
            "boot_time": datetime.datetime.fromtimestamp(boot_time).astimezone().isoformat(timespec="seconds"),
            "uptime_seconds": max(time.time() - boot_time, 0.0),
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Calculates multi-dimensional category scores and overall health score."""
        cpu = self.get_cpu_stats()
        mem = self.get_memory_stats()
        stor = self.get_storage_stats()
        net = self.get_network_stats()
        
        # Category 1: CPU Health (100 - usage penalty)
        cpu_score = max(100 - int(cpu['cpu_usage'] * 0.8), 10)
        cpu_status = "healthy" if cpu_score > 70 else ("degraded" if cpu_score > 40 else "critical")
        
        # Category 2: Memory Health
        mem_score = max(100 - int(mem['memory_percent'] * 0.9), 5)
        mem_status = "healthy" if mem_score > 70 else ("degraded" if mem_score > 40 else "critical")
        
        # Category 3: Storage Health
        if stor['usage_percent'] is None:
            stor_score, stor_status = None, "unknown"
        else:
            stor_score = max(100 - int(stor['usage_percent'] * 0.95), 10)
            stor_status = "healthy" if stor_score > 70 else ("degraded" if stor_score > 40 else "critical")
        
        # Category 4: Network Health
        net_score = 95 if net['internet_available'] else 30
        net_status = "healthy" if net['internet_available'] else "critical"
        
        # Weighted Overall Health Score
        measured_weight = 0.30 + 0.35 + 0.15
        weighted_score = 0.30 * cpu_score + 0.35 * mem_score + 0.15 * net_score
        if stor_score is not None:
            measured_weight += 0.20
            weighted_score += 0.20 * stor_score
        overall = int(weighted_score / measured_weight)
        
        categories = [
            {
                "name": "CPU & Processing",
                "score": cpu_score,
                "status": cpu_status,
                "explanation": f"Average CPU utilization across cores is at {cpu['cpu_usage']}%.",
                "recommendation": "Optimal operation" if cpu_score > 70 else "Inspect heavy processes"
            },
            {
                "name": "Memory & Swap",
                "score": mem_score,
                "status": mem_status,
                "explanation": f"RAM usage is {mem['memory_percent']}% with {mem['free_gb']} GB available.",
                "recommendation": "Stable capacity" if mem_score > 70 else "Consider closing memory-heavy tasks"
            },
            {
                "name": "Storage & Filesystem",
                "score": stor_score,
                "status": stor_status,
                "explanation": (
                    f"Detected volumes are at {stor['usage_percent']}% capacity "
                    f"({stor['available_gb']} GB free)."
                    if stor['usage_percent'] is not None
                    else "No mounted volumes could be measured."
                ),
                "recommendation": (
                    ""
                    if stor['usage_percent'] is None
                    else "Storage healthy"
                    if stor_score > 70
                    else "Review files and applications on the detected volumes"
                )
            },
            {
                "name": "Network & Sockets",
                "score": net_score,
                "status": net_status,
                "explanation": "Internet uplink verified." if net['internet_available'] else "Internet gateway unreachable.",
                "recommendation": "Network functional" if net['internet_available'] else "Check gateway & DNS"
            }
        ]
        
        return {
            "score": overall,
            "categories": categories
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """Returns consolidated CPU, Memory, Storage, Network, and Health stats in a single fast pass."""
        cpu = self.get_cpu_stats()
        mem = self.get_memory_stats()
        stor = self.get_storage_stats()
        net = self.get_network_stats()

        # Category 1: CPU Health (100 - usage penalty)
        cpu_score = max(100 - int(cpu['cpu_usage'] * 0.8), 10)
        cpu_status = "healthy" if cpu_score > 70 else ("degraded" if cpu_score > 40 else "critical")

        # Category 2: Memory Health
        mem_score = max(100 - int(mem['memory_percent'] * 0.9), 5)
        mem_status = "healthy" if mem_score > 70 else ("degraded" if mem_score > 40 else "critical")

        # Category 3: Storage Health
        if stor['usage_percent'] is None:
            stor_score, stor_status = None, "unknown"
        else:
            stor_score = max(100 - int(stor['usage_percent'] * 0.95), 10)
            stor_status = "healthy" if stor_score > 70 else ("degraded" if stor_score > 40 else "critical")

        # Category 4: Network Health
        net_score = 95 if net['internet_available'] else 30
        net_status = "healthy" if net['internet_available'] else "critical"

        # Weighted Overall Health Score
        measured_weight = 0.30 + 0.35 + 0.15
        weighted_score = 0.30 * cpu_score + 0.35 * mem_score + 0.15 * net_score
        if stor_score is not None:
            measured_weight += 0.20
            weighted_score += 0.20 * stor_score
        overall = int(weighted_score / measured_weight)

        health = {
            "score": overall,
            "categories": [
                {
                    "name": "CPU & Processing",
                    "score": cpu_score,
                    "status": cpu_status,
                    "explanation": f"Average CPU utilization across cores is at {cpu['cpu_usage']}%.",
                    "recommendation": "Optimal operation" if cpu_score > 70 else "Inspect heavy processes"
                },
                {
                    "name": "Memory & Swap",
                    "score": mem_score,
                    "status": mem_status,
                    "explanation": f"RAM usage is {mem['memory_percent']}% with {mem['free_gb']} GB available.",
                    "recommendation": "Stable capacity" if mem_score > 70 else "Consider closing memory-heavy tasks"
                },
                {
                    "name": "Storage & Filesystem",
                    "score": stor_score,
                    "status": stor_status,
                    "explanation": (
                        f"Detected volumes are at {stor['usage_percent']}% capacity "
                        f"({stor['available_gb']} GB free)."
                        if stor['usage_percent'] is not None
                        else "No mounted volumes could be measured."
                    ),
                    "recommendation": (
                        ""
                        if stor['usage_percent'] is None
                        else "Storage healthy"
                        if stor_score > 70
                        else "Review files and applications on the detected volumes"
                    )
                },
                {
                    "name": "Network & Sockets",
                    "score": net_score,
                    "status": net_status,
                    "explanation": "Internet uplink verified." if net['internet_available'] else "Internet gateway unreachable.",
                    "recommendation": "Network functional" if net['internet_available'] else "Check gateway & DNS"
                }
            ]
        }

        return {
            "cpu": cpu,
            "memory": mem,
            "storage": stor,
            "network": net,
            "health": health
        }

telemetry_collector = TelemetryCollector()
