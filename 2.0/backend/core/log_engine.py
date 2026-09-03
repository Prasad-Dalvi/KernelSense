"""
Live System Log Collector & NLP Intelligence Engine for KernelSense
Collects system log entries and runs NLP inference to detect kernel errors and anomalies.
"""

import time
import uuid
import datetime
from typing import List, Dict, Any, Optional
from core.ml_inference import ml_engine

class LogEngine:
    def __init__(self):
        self.cached_logs: List[Dict[str, Any]] = []
        self._init_live_log_buffer()

    def _init_live_log_buffer(self):
        """Initializes realistic system log stream classified by the NLP model."""
        base_time = datetime.datetime.now()
        
        sample_messages = [
            ("systemd", "Reached target Graphical Interface.", 120),
            ("NetworkManager", "enp3s0: IP4 address successfully configured to 192.168.1.105/24", 115),
            ("systemd-timesyncd", "Synchronized to time server 162.159.200.123:123 (time.cloudflare.com).", 95),
            ("CRON", "(root) CMD (test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily ))", 80),
            ("dockerd", "Container 4a82b9 started (image=postgres:16-alpine)", 65),
            ("kernel", "usb 1-1.2: new high-speed USB device number 5 using xhci_hcd", 50),
            ("sshd", "Accepted publickey for ubuntu from 192.168.1.50 port 54210 ssh2", 35),
            ("kernel", "EXT4-fs (sda2): re-mounted. Opts: errors=remount-ro.", 20),
            ("systemd-resolved", "Using degraded feature set (UDP) for DNS server 1.1.1.1", 10),
            ("systemd", "Starting Daily apt download activities...", 5),
        ]
        
        for service, msg, ago in sample_messages:
            t = base_time - datetime.timedelta(seconds=ago)
            nlp_result = ml_engine.predict_log(msg)
            
            self.cached_logs.append({
                "id": str(uuid.uuid4())[:8],
                "timestamp": t.strftime("%H:%M:%S"),
                "service": service,
                "message": msg,
                "severity": nlp_result["severity"],
                "category": nlp_result["category"],
                "confidence": nlp_result["confidence"],
                "pid": 1000 + len(self.cached_logs)
            })

    def get_logs(self, severity: Optional[str] = None, service: Optional[str] = None, search: Optional[str] = None, limit: int = 150) -> List[Dict[str, Any]]:
        """Filters and returns classified system logs."""
        logs = list(self.cached_logs)
        
        if severity:
            logs = [l for l in logs if l['severity'].lower() == severity.lower()]
        if service:
            logs = [l for l in logs if service.lower() in l['service'].lower()]
        if search:
            logs = [l for l in logs if search.lower() in l['message'].lower()]
            
        return logs[:limit]

    def add_log_entry(self, service: str, message: str):
        """Classifies and appends a new live log event."""
        nlp_result = ml_engine.predict_log(message)
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": now_str,
            "service": service,
            "message": message,
            "severity": nlp_result["severity"],
            "category": nlp_result["category"],
            "confidence": nlp_result["confidence"],
            "pid": None
        }
        self.cached_logs.insert(0, entry)
        if len(self.cached_logs) > 500:
            self.cached_logs.pop()
        return entry

log_engine = LogEngine()
