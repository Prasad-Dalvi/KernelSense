"""
Ubuntu WSL Ollama & Local Llama AI Management Engine for KernelSense
Provides local LLM inference, daemon management, and model pulling inside Ubuntu Linux (WSL2).
"""

import os
import sys
import time
import requests
import subprocess
import platform
from typing import Dict, Any, Optional

class OllamaManager:
    def __init__(self, distro: str = "Ubuntu", default_model: str = "llama3.2:1b", base_url: str = "http://127.0.0.1:11434"):
        self.distro = distro
        self.default_model = default_model
        self.base_url = base_url
        self.is_windows = platform.system() == "Windows"

    def is_installed_in_wsl(self) -> bool:
        """Checks if ollama binary exists inside Ubuntu WSL."""
        if not self.is_windows:
            res = subprocess.run(["which", "ollama"], capture_output=True, text=True)
            return res.returncode == 0
        try:
            res = subprocess.run(["wsl.exe", "-d", self.distro, "--", "which", "ollama"], capture_output=True, text=True, timeout=3)
            return res.returncode == 0 and "ollama" in res.stdout
        except Exception:
            return False

    def is_service_online(self) -> bool:
        """Checks if Ollama HTTP API is responding."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def start_service(self) -> Dict[str, Any]:
        """Starts the Ollama server inside Ubuntu WSL in the background."""
        if self.is_service_online():
            return {"success": True, "message": "Ollama service is already running."}

        if not self.is_installed_in_wsl():
            return {"success": False, "message": "Ollama is not installed in Ubuntu WSL yet."}

        try:
            if self.is_windows:
                subprocess.Popen(["wsl.exe", "-d", self.distro, "--", "bash", "-c", "OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama.log 2>&1 &"])
            else:
                subprocess.Popen(["bash", "-c", "OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama.log 2>&1 &"])
            time.sleep(2)
            online = self.is_service_online()
            return {
                "success": online,
                "message": "Ollama service started in Ubuntu WSL." if online else "Ollama starting in background..."
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to start Ollama: {str(e)}"}

    def generate_reasoning(self, prompt: str, system_prompt: str = "You are KernelSense AI, an expert Linux/Windows OS operations assistant.", timeout_sec: int = 5) -> Optional[str]:
        """
        Queries local Ollama Llama model for natural language reasoning.
        Uses HTTP endpoint first, with direct WSL CLI fallback.
        Returns None gracefully if Ollama is offline so system diagnosis never breaks.
        """
        # Try HTTP API first
        if self.is_service_online():
            try:
                payload = {
                    "model": self.default_model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 180
                    }
                }
                r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=timeout_sec)
                if r.status_code == 200:
                    data = r.json()
                    res = data.get("response", "").strip()
                    if res:
                        return res
            except Exception:
                pass

        # Direct WSL CLI fallback
        if self.is_installed_in_wsl():
            try:
                cmd = ["wsl.exe", "-d", self.distro, "--", "ollama", "run", self.default_model, prompt] if self.is_windows else ["ollama", "run", self.default_model, prompt]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                return None

        return None

ollama_mgr = OllamaManager()
