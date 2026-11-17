"""
Member 1: Intelligent ReAct AI Diagnostic & Operations Agent for KernelSense
Orchestrates AI intent classification, multi-tool reasoning plans,
Win32 desktop application launching, and ML telemetry diagnostics.
"""

from typing import Dict, Any, Optional
from ai.planner import planner

class DiagnosticAgent:
    def ask(
        self,
        query: str,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Routes user queries through the structured AI Planner & Tool pipeline."""
        return planner.plan_and_execute(
            query,
            provider=provider,
            api_key=api_key,
            model=model,
        )

ai_agent = DiagnosticAgent()
