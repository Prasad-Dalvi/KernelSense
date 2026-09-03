"""
Unified Tool Execution Registry for KernelSense AI
"""

from typing import Dict, Any, List
from windows.apps import launch_application, launch_browser_url, resolve_app
from core.live_telemetry import telemetry_collector
from core.process_engine import process_engine
from core.log_engine import log_engine
from core.ml_inference import ml_engine
from core.command_safety import command_safety_engine

class ToolRegistry:
    @staticmethod
    def open_application(app_name: str) -> Dict[str, Any]:
        """Tool to launch desktop application directly."""
        return launch_application(app_name)

    @staticmethod
    def open_browser_url(url: str, browser: str = "chrome") -> Dict[str, Any]:
        """Tool to launch specific URL on a chosen web browser."""
        return launch_browser_url(url, browser)

    @staticmethod
    def evaluate_telemetry_anomaly() -> Dict[str, Any]:
        """Tool to run Isolation Forest & ML anomaly classifier."""
        vector = telemetry_collector.get_feature_vector_for_ml()
        return ml_engine.predict_telemetry_anomaly(vector)

    @staticmethod
    def poll_live_telemetry() -> Dict[str, Any]:
        """Tool to fetch real-time CPU, RAM, Disk, Network metrics."""
        return {
            "cpu": telemetry_collector.get_cpu_stats(),
            "memory": telemetry_collector.get_memory_stats(),
            "storage": telemetry_collector.get_storage_stats(),
            "network": telemetry_collector.get_network_stats(),
            "health": telemetry_collector.get_system_health()
        }

    @staticmethod
    def inspect_processes(limit: int = 5) -> Dict[str, Any]:
        """Tool to inspect active top memory and CPU tasks."""
        return {
            "top_memory": process_engine.get_top_memory_processes(limit=limit),
            "top_cpu": process_engine.get_top_cpu_processes(limit=limit)
        }

    @staticmethod
    def classify_system_logs(limit: int = 20) -> List[Dict[str, Any]]:
        """Tool to aggregate system logs and classify severity via NLP."""
        return log_engine.get_logs(limit=limit)

    @staticmethod
    def execute_shell_command(command: str) -> Dict[str, Any]:
        """Tool to safely execute an approved system command."""
        return command_safety_engine.execute_command(command)

tools = ToolRegistry()
