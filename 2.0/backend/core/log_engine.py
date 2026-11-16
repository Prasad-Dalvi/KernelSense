"""Read real Windows Event Log entries and classify their message text."""

import json
import subprocess
import time
from typing import Any, Dict, List, Optional

from core.ml_inference import ml_engine


class LogEngine:
    def __init__(self, cache_seconds: float = 5.0, limit: int = 150):
        self.cache_seconds = cache_seconds
        self.limit = limit
        self.cached_logs: List[Dict[str, Any]] = []
        self._last_refresh: Optional[float] = None

    def _read_windows_events(self) -> List[Dict[str, Any]]:
        script = f"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {{
  $events = @(Get-WinEvent -LogName System,Application -MaxEvents {self.limit} -ErrorAction Stop)
  $result = $events | Select-Object `
    @{{Name='id';Expression={{"$($_.LogName)-$($_.RecordId)"}}}}, `
    @{{Name='timestamp';Expression={{$_.TimeCreated.ToString('o')}}}}, `
    @{{Name='service';Expression={{$_.ProviderName}}}}, `
    @{{Name='message';Expression={{if ($_.Message) {{ $_.Message -replace '\\r?\\n',' ' }} else {{ '' }}}}}}, `
    @{{Name='level';Expression={{$_.LevelDisplayName}}}}, `
    @{{Name='level_number';Expression={{$_.Level}}}}, `
    @{{Name='pid';Expression={{$_.ProcessId}}}}
  if ($null -eq $result) {{ '[]' }} else {{ $result | ConvertTo-Json -Compress }}
}} catch {{
  if ($_.FullyQualifiedErrorId -like '*NoMatchingEventsFound*') {{
    '[]'
  }} else {{
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
  }}
}}
"""
        try:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"Unable to read Windows Event Log: {exc}") from exc

        if result.returncode != 0:
            detail = result.stderr.strip() or "PowerShell returned an error."
            raise RuntimeError(f"Unable to read Windows Event Log: {detail}")

        try:
            events = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise RuntimeError("Windows Event Log returned invalid JSON.") from exc

        if events is None:
            return []
        if isinstance(events, dict):
            events = [events]
        if not isinstance(events, list):
            raise RuntimeError("Windows Event Log returned an unexpected response.")

        logs = []
        for event in events:
            if not isinstance(event, dict):
                continue
            message = str(event.get("message") or "").strip()
            prediction = ml_engine.predict_log(message)
            level = str(event.get("level") or "").lower()
            level_number = event.get("level_number")
            if "critical" in level or "error" in level or level_number in (1, 2):
                severity = "critical"
            elif "warning" in level or level_number == 3:
                severity = "warning"
            else:
                severity = "info"
            logs.append({
                "id": str(event.get("id") or ""),
                "timestamp": event.get("timestamp"),
                "service": event.get("service"),
                "message": message,
                "severity": severity,
                "category": prediction["category"],
                "confidence": prediction["confidence"],
                "pid": event.get("pid"),
            })
        return logs

    def get_logs(
        self,
        severity: Optional[str] = None,
        service: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 150,
    ) -> List[Dict[str, Any]]:
        """Returns filtered, recently collected events from Windows System and Application logs."""
        if (
            self._last_refresh is None
            or time.monotonic() - self._last_refresh >= self.cache_seconds
        ):
            self.cached_logs = self._read_windows_events()
            self._last_refresh = time.monotonic()

        logs = self.cached_logs
        if severity:
            logs = [entry for entry in logs if entry["severity"].lower() == severity.lower()]
        if service:
            logs = [
                entry for entry in logs
                if service.lower() in (entry["service"] or "").lower()
            ]
        if search:
            logs = [entry for entry in logs if search.lower() in entry["message"].lower()]
        return logs[:limit]


log_engine = LogEngine()
