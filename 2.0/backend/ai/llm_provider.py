"""
Gemini-Powered Universal LLM Provider for KernelSense
Primary intelligence engine using Google Gemini API for:
1. Real intent classification — understands ANY natural language query
2. Zero-shot OS command generation for Linux/Windows
3. Grounded reasoning with live hardware telemetry
4. Fallback chain: Gemini → Groq → Ollama
"""

import os
import json
import logging
import requests
import platform
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment — .env lives in backend/, one level up from ai/
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=_env_path, override=True)

logger = logging.getLogger("kernelsense.llm")

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# ─── Compact System Prompt (fast, single-purpose JSON classification) ──────────
# Kept short to minimize Gemini thinking time. Target: < 8s response.
SYSTEM_PROMPT = """You are KernelSense AI — an OS assistant for Windows 11 + Ubuntu WSL2.
Output ONLY a single valid JSON object. No markdown, no explanation outside JSON.

JSON schema:
{
  "intent": "GREETING"|"FILE_SEARCH"|"LINUX_CORE_COMMAND"|"OPEN_URL_IN_APP"|"OPEN_APPLICATION"|"SYSTEM_DIAGNOSIS"|"MEMORY_DIAGNOSIS"|"CPU_DIAGNOSIS"|"GENERAL_QUERY",
  "action_type": "OPEN_URL"|"OPEN_APP"|"LINUX_SHELL"|"FILE_OPEN"|"DIAGNOSTIC"|"CHAT"|"NONE",
  "target_url": "<https:// URL or null>",
  "target_app": "<app name or null>",
  "browser": "<chrome|brave|edge|firefox>",
  "search_target": "<filename if FILE_SEARCH, else null>",
  "linux_command": "<exact bash command(s) if LINUX_CORE_COMMAND, else null>",
  "linux_task_type": "<IP_ADDRESS|USER_IDENTITY|HOSTNAME_OS|OPEN_PORTS|CPU_INFO|BLOCK_DEVICES|DIR_LIST|RAW_COMMAND|null>",
  "linux_title": "<friendly title like '🌐 IP Address Discovery' or null>",
  "linux_explanation": "<what the command does, or null>",
  "response_markdown": "<rich markdown answer — required for GENERAL_QUERY, GREETING, SYSTEM_DIAGNOSIS>",
  "root_cause_nodes": [{"id":"n1","label":"...","type":"process"|"system"|"impact"}],
  "root_cause_edges": [{"from":"n1","to":"n2"}],
  "proposed_commands": [{"command":"...","explanation":"...","risk_level":"LOW"|"MEDIUM"|"HIGH"}],
  "recommendations": ["...", "..."]
}

RULES:
- GREETING: hi/hello/hey/who are you/what can you do
- FILE_SEARCH: find/search/open/read + filename (set search_target=filename)
- LINUX_CORE_COMMAND: any Linux/OS info request — IP, username, hostname, ports, CPU, disk, whoami, lscpu, etc.
  Linux commands: IP→"hostname -I; ip -br a", whoami→"whoami; id; w", ports→"ss -tulnp", cpu→"lscpu", disk→"df -h; lsblk", hostname→"hostname; uname -a; cat /etc/os-release"
- OPEN_APPLICATION: open desktop applications, software, tools, or PC games installed on the system (e.g. valorant, riot games / riot client, steam, discord, vlc, packet tracer, codeblocks, notepad, calculator, paint, terminal, vscode, excel, word, spotify, etc.). Set target_app to the app/game name.
- OPEN_URL_IN_APP: open websites or web pages in browser (e.g. youtube, google, github, stackoverflow, reddit, netflix, etc. or queries with explicit 'on chrome'/'on brave'). Set target_url and browser.
- SYSTEM_DIAGNOSIS/MEMORY_DIAGNOSIS/CPU_DIAGNOSIS: performance questions — use telemetry context
- GENERAL_QUERY: everything else — answer fully in response_markdown like an expert engineer"""


class GeminiProvider:
    """Primary intelligence engine — Google Gemini REST API."""

    def __init__(self):
        self.api_key  = GEMINI_API_KEY
        self.model    = GEMINI_MODEL
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def query(self, user_message: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None
        try:
            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": user_message}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                }
            }
            resp = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                timeout=60        # 60s — Gemini thinking models can be slow
            )
            if resp.status_code == 200:
                data  = resp.json()
                parts = data["candidates"][0]["content"]["parts"]

                # Thinking models (gemini-3.x) return thoughtSignature + text parts
                # Collect ALL text parts and find the JSON one
                raw_text = ""
                for part in parts:
                    txt = part.get("text", "").strip()
                    if txt:
                        raw_text = txt
                        break   # First non-empty text part is the answer

                if not raw_text:
                    logger.warning("Gemini returned empty text parts")
                    return None

                # Extract JSON from text (strip any surrounding prose/fences)
                start = raw_text.find("{")
                end   = raw_text.rfind("}")
                if start != -1 and end != -1:
                    raw_text = raw_text[start:end+1]

                return json.loads(raw_text)

            else:
                logger.warning(f"Gemini {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Gemini query failed: {e}")
        return None


class GroqProvider:
    """Fast Groq cloud fallback — Llama 3.3 70B."""

    def query(self, user_message: str) -> Optional[Dict[str, Any]]:
        if not GROQ_API_KEY:
            return None
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": user_message}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                },
                timeout=15
            )
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"]
                return json.loads(raw)
        except Exception as e:
            logger.warning(f"Groq query failed: {e}")
        return None


class OllamaProvider:
    """Local Ollama offline fallback."""

    def is_online(self) -> bool:
        try:
            return requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.5).status_code == 200
        except Exception:
            return False

    def query(self, user_message: str) -> Optional[Dict[str, Any]]:
        if not self.is_online():
            return None
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": f"{SYSTEM_PROMPT}\n\nUser: {user_message}",
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1, "num_predict": 2048}
                },
                timeout=20
            )
            if resp.status_code == 200:
                raw = resp.json().get("response", "").strip()
                start, end = raw.find("{"), raw.rfind("}")
                if start != -1 and end != -1:
                    return json.loads(raw[start:end+1])
        except Exception as e:
            logger.warning(f"Ollama query failed: {e}")
        return None


class UniversalLLMProvider:
    """
    Multi-LLM gateway: Gemini (primary) → Groq → Ollama.
    All providers use the same compact SYSTEM_PROMPT.
    """

    def __init__(self):
        self.gemini = GeminiProvider()
        self.groq   = GroqProvider()
        self.ollama = OllamaProvider()
        self.is_windows = platform.system() == "Windows"

    def reason_and_plan(self, query: str, telemetry_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Send query + live telemetry to Gemini → Groq → Ollama. Returns structured JSON."""
        user_message = f"User Request: {query}"
        if telemetry_context:
            # Include only key telemetry to keep prompt short
            tc = telemetry_context
            user_message += (
                f"\n\nLive System Telemetry: CPU={tc.get('cpu_usage_percent',0):.1f}%  "
                f"RAM={tc.get('memory_percent',0):.1f}% ({tc.get('memory_used_gb',0):.1f}/{tc.get('memory_total_gb',0):.1f}GB)  "
                f"Disk={tc.get('disk_usage_percent',0):.1f}%  "
                f"Health={tc.get('system_health_score',95)}/100\n"
                f"Top RAM processes: {[p.get('name') for p in tc.get('top_memory_processes', [])[:3]]}\n"
                f"Top CPU processes: {[p.get('name') for p in tc.get('top_cpu_processes', [])[:3]]}"
            )

        # 1. Gemini (primary)
        result = self.gemini.query(user_message)
        if result:
            result["provider"] = f"gemini/{GEMINI_MODEL}"
            return result

        # 2. Groq (fast cloud fallback)
        result = self.groq.query(user_message)
        if result:
            result["provider"] = "groq/llama-3.3-70b"
            return result

        # 3. Ollama (local offline fallback)
        result = self.ollama.query(user_message)
        if result:
            result["provider"] = f"ollama/{OLLAMA_MODEL}"
            return result

        return None

    # Backward compatibility stubs
    def query_groq(self, system_prompt, user_prompt):
        return self.groq.query(user_prompt)
    def query_openai(self, system_prompt, user_prompt):
        return None
    def query_ollama_http(self, system_prompt, user_prompt):
        return self.ollama.query(user_prompt)
    def is_ollama_online(self):
        return self.ollama.is_online()


llm_gateway = UniversalLLMProvider()
