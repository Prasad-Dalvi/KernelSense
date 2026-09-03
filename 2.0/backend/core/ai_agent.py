"""
Member 1: Intelligent ReAct AI Diagnostic & Operations Agent for KernelSense
Orchestrates AI intent classification, multi-tool reasoning plans,
Win32 desktop application launching, and ML telemetry diagnostics.
"""

from typing import Dict, Any
from ai.planner import planner

class DiagnosticAgent:
    def ask(self, query: str) -> Dict[str, Any]:
        """Routes user queries through the structured AI Planner & Tool pipeline."""
        return planner.plan_and_execute(query)

ai_agent = DiagnosticAgent()
