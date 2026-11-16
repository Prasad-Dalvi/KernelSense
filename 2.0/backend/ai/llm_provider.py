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
GROK_API_KEY    = os.getenv("GROK_API_KEY", "")
GROK_MODEL      = os.getenv("GROK_MODEL") or "grok-4.7"
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# ─── Compact System Prompt (fast, single-purpose JSON classification) ──────────
# Kept short to minimize Gemini thinking time. Target: < 8s response.
SYSTEM_PROMPT = """You are KernelSense AI — a system assistant for the host described in each request.
Use the supplied host and telemetry data as the source of truth. Do not assume a particular Windows version or report a WSL distribution as the host operating system.
Commands that explicitly target Ubuntu WSL must be described as WSL operations, separate from the host.
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
- Use the supplied host data for questions about the host OS, CPU, memory, or disks. Do not use WSL's `uname` output as the host OS.
- LINUX_CORE_COMMAND: use only for requested terminal operations that target Ubuntu WSL; label these as WSL operations.
- WSL commands: IP→"hostname -I; ip -br a", whoami→"whoami; id; w", ports→"ss -tulnp", CPU→"lscpu", disk→"df -h; lsblk", hostname→"hostname; uname -a; cat /etc/os-release"
- OPEN_APPLICATION: open desktop applications, software, tools, or PC games installed on the system (e.g. valorant, riot games / riot client, steam, discord, vlc, packet tracer, codeblocks, notepad, calculator, paint, terminal, vscode, excel, word, spotify, etc.). Set target_app to the app/game name.
- OPEN_URL_IN_APP: open websites or web pages in browser (e.g. youtube, google, github, stackoverflow, reddit, netflix, etc. or queries with explicit 'on chrome'/'on brave'). Set target_url and browser.
- SYSTEM_DIAGNOSIS/MEMORY_DIAGNOSIS/CPU_DIAGNOSIS: performance questions — use telemetry context
- GENERAL_QUERY: everything else — answer fully in response_markdown like an expert engineer"""


class GeminiProvider:
    """Primary intelligence engine — Google Gemini REST API with multi-model fallback resilience."""

    def __init__(self):
        self.api_key  = GEMINI_API_KEY
        self.preferred_model = GEMINI_MODEL or "gemini-3.1-flash-lite"
        # Ordered list of candidate models supported by Gemini API
        self.candidate_models = [
            "gemini-3.1-flash-lite-preview",
            self.preferred_model,
            "gemini-flash-latest",
        ]
        # De-duplicate preserving order
        seen = set()
        self.models = [m for m in self.candidate_models if not (m in seen or seen.add(m))]
        self.active_model = self.models[0]

    def is_available(self) -> bool:
        return bool(self.api_key)

    def query(self, user_message: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        api_key = api_key or self.api_key or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return None

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 4096,
            }
        }

        # Try active_model first, then fallback to other models if needed
        models_to_try = [self.active_model] + [m for m in self.models if m != self.active_model]

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            try:
                resp = requests.post(
                    url,
                    headers={"x-goog-api-key": api_key},
                    json=payload,
                    timeout=8
                )
                if resp.status_code == 200:
                    data  = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])

                    # Thinking models return thoughtSignature + text parts
                    raw_text = ""
                    for part in parts:
                        txt = part.get("text", "").strip()
                        if txt:
                            raw_text = txt
                            break

                    if not raw_text:
                        continue

                    # Extract JSON from text
                    start = raw_text.find("{")
                    end   = raw_text.rfind("}")
                    if start != -1 and end != -1:
                        raw_text = raw_text[start:end+1]

                    parsed = json.loads(raw_text)
                    parsed["_model_used"] = model_name
                    self.active_model = model_name
                    return parsed

                elif resp.status_code in (404, 429, 503):
                    logger.warning(f"Gemini {model_name} returned {resp.status_code}, switching to fallback model...")
                    continue
                else:
                    logger.warning(f"Gemini {resp.status_code} on {model_name}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"Gemini query failed on {model_name}: {e}")
                continue
        return None


class GrokProvider:
    """xAI Grok provider using its OpenAI-compatible chat completions API."""

    active_model = GROK_MODEL

    def query(self, user_message: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        api_key = api_key or GROK_API_KEY or os.getenv("GROK_API_KEY", "")
        if not api_key:
            return None

        try:
            resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": GROK_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
                timeout=25
            )
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"]
                start, end = raw.find("{"), raw.rfind("}")
                if start != -1 and end != -1:
                    parsed = json.loads(raw[start:end + 1])
                    parsed["_model_used"] = GROK_MODEL
                    return parsed
            else:
                logger.warning("Grok returned HTTP %s", resp.status_code)
        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            logger.warning("Grok query failed: %s", e)
        return None


class GroqProvider:
    """Fast Groq cloud provider / fallback — ultra-low latency inference."""

    def __init__(self):
        self.candidate_models = [
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "groq/compound-mini",
            "groq/compound",
            "llama-3.3-70b-versatile",
        ]
        self.active_model = self.candidate_models[0]

    def is_available(self) -> bool:
        key = os.getenv("GROQ_API_KEY", "") or GROQ_API_KEY
        return bool(key)

    def query(self, user_message: str) -> Optional[Dict[str, Any]]:
        api_key = os.getenv("GROQ_API_KEY", "") or GROQ_API_KEY
        if not api_key:
            return None

        models_to_try = [self.active_model] + [m for m in self.candidate_models if m != self.active_model]

        for model in models_to_try:
            try:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user",   "content": user_message}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1
                    },
                    timeout=10
                )
                if resp.status_code == 200:
                    raw = resp.json()["choices"][0]["message"]["content"]
                    parsed = json.loads(raw)
                    parsed["_model_used"] = model
                    self.active_model = model
                    return parsed
                elif resp.status_code in (404, 429, 503):
                    logger.warning(f"Groq {model} returned {resp.status_code}, switching to fallback model...")
                    continue
                else:
                    logger.warning(f"Groq {resp.status_code} on {model}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"Groq query failed on {model}: {e}")
                continue
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
    Routes to the selected Gemini or Grok provider, followed by configured fallbacks.
    All providers use the same compact SYSTEM_PROMPT.
    """

    def __init__(self):
        self.gemini = GeminiProvider()
        self.grok   = GrokProvider()
        self.groq   = GroqProvider()
        self.ollama = OllamaProvider()
        self.is_windows = platform.system() == "Windows"

    def reason_and_plan(
        self,
        query: str,
        telemetry_context: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Send query + live telemetry through provider chain. Returns structured JSON."""
        api_key = api_key.strip() if api_key else None
        user_message = f"User Request: {query}"
        if telemetry_context:
            user_message += (
                "\n\nCurrent measured host data (JSON; null means unavailable, "
                "do not infer a value):\n"
                + json.dumps(telemetry_context, separators=(",", ":"))
            )

        provider_pref = (provider or os.getenv("LLM_PROVIDER", "gemini") or "gemini").lower().strip()
        if provider_pref == "groq":
            providers = [
                ("groq", self.groq, None),
                ("gemini", self.gemini, None),
                ("grok", self.grok, None),
                ("ollama", self.ollama, None),
            ]
        elif provider_pref == "grok":
            providers = [
                ("grok", self.grok, api_key),
                ("gemini", self.gemini, None),
                ("groq", self.groq, None),
                ("ollama", self.ollama, None),
            ]
        else:
            providers = [
                ("gemini", self.gemini, api_key),
                ("grok", self.grok, None),
                ("groq", self.groq, None),
                ("ollama", self.ollama, None),
            ]

        for p_name, p_inst, provider_key in providers:
            try:
                if p_name in ("gemini", "grok"):
                    result = p_inst.query(user_message, provider_key)
                else:
                    result = p_inst.query(user_message)
                if result:
                    model_used = result.pop("_model_used", getattr(p_inst, "active_model", p_name))
                    result["provider"] = f"{p_name}/{model_used}"
                    return result
            except Exception as e:
                logger.warning(f"Provider {p_name} error: {e}")

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
