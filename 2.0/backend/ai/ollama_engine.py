"""
Local Ollama & Llama 3.2 Reasoning Engine for KernelSense
Performs zero-shot natural language intent classification, dynamic tool routing,
and intelligent operations synthesis using local Llama 3.2 models via Ollama.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger("kernelsense.ollama")

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


class OllamaEngine:
    """
    Communicates with local Ollama daemon for Llama 3.2 zero-shot reasoning.
    """

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = 8.0

    def is_available(self) -> Dict[str, Any]:
        """Checks if local Ollama daemon is reachable and lists installed models."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "available": True,
                    "models": models,
                    "active_model": self.model if self.model in models or any(self.model in m for m in models) else (models[0] if models else self.model)
                }
        except Exception as e:
            logger.debug(f"Ollama not reachable: {e}")
        return {"available": False, "models": [], "active_model": self.model}

    def reason_and_classify(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Sends the user's natural language input to Llama 3.2 for zero-shot reasoning,
        intent classification, entity extraction, and custom response synthesis.
        """
        status = self.is_available()
        if not status["available"]:
            return None

        active_model = status.get("active_model", self.model)

        system_prompt = """You are KernelSense AI, an intelligent Linux Operations & System Reasoning Agent.
Analyze the user's natural language query and determine their true intent and required action.

You MUST respond strictly in valid JSON format matching this schema:
{
  "intent": "APPLICATION_LAUNCH" | "COMMAND_EXPLANATION" | "SYSTEM_COMMAND_EXECUTION" | "SYSTEM_DIAGNOSIS" | "PROCESS_ANALYSIS" | "NETWORK_DIAGNOSIS" | "STORAGE_OPTIMIZATION" | "LOG_ANALYSIS" | "GENERAL_QUERY",
  "target_app_or_command": "<binary or command, e.g. mspaint, calc, notepad, chrome, htop, grep, chmod, systemctl, ping, find, taskkill>",
  "activity_type": "<short description of activity, e.g. painting, budget calculation, viewing logs, port scan>",
  "is_gui_app": true | false,
  "confidence": <float 0.0 - 1.0>,
  "reasoning": "<step-by-step reasoning explaining why this action was selected>",
  "response_markdown": "<clear, helpful, well-structured Markdown response for the user explaining the action, command breakdown, or analysis>",
  "proposed_commands": [
    {
      "command": "<exact shell command for Ubuntu / Windows>",
      "explanation": "<what this command does>",
      "risk_level": "LOW" | "MEDIUM" | "HIGH"
    }
  ],
  "recommendations": ["<actionable tip 1>", "<actionable tip 2>"]
}

Rules:
1. Do not use hardcoded templates. Reason dynamically about whatever the user wants to do.
2. If user says "i want to do painting", "draw a picture", etc. -> intent="APPLICATION_LAUNCH", target_app_or_command="mspaint", is_gui_app=true.
3. If user says "calculate expenses", "solve math", etc. -> intent="APPLICATION_LAUNCH", target_app_or_command="calc", is_gui_app=true.
4. If user asks "what is htop", "explain chmod 755", etc. -> intent="COMMAND_EXPLANATION", target_app_or_command="htop", provide full manual, flags, and practical examples in response_markdown.
5. If user asks to check network, disk, cpu, or processes -> select the appropriate DIAGNOSIS intent.
6. Output ONLY valid JSON, without any surrounding markdown code fences.
"""

        user_content = f"User Request: {query}\n"
        if context:
            user_content += f"System Context: {json.dumps(context)}\n"

        payload = {
            "model": active_model,
            "prompt": f"{system_prompt}\n\n{user_content}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 1024
            }
        }

        try:
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                raw_out = resp.json().get("response", "").strip()
                # Clean possible markdown wrapping if any
                if raw_out.startswith("```json"):
                    raw_out = raw_out[7:]
                if raw_out.startswith("```"):
                    raw_out = raw_out[3:]
                if raw_out.endswith("```"):
                    raw_out = raw_out[:-3]
                raw_out = raw_out.strip()

                parsed = json.loads(raw_out)
                parsed["llm_engine"] = f"ollama/{active_model}"
                return parsed
        except Exception as e:
            logger.warning(f"Ollama reasoning error: {e}")

        return None


ollama_engine = OllamaEngine()
