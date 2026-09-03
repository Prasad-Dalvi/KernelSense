"""
Intelligent NLP & Semantic Intent Classification Engine for KernelSense
Integrates local Ollama (Llama 3.2) zero-shot reasoning as primary layer,
with granular semantic ontology and direct verb-object resolution.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from ai.ollama_engine import ollama_engine

logger = logging.getLogger("kernelsense.nlp")

# ─────────────────────────────────────────────────────────────────────────────
# Granular Semantic Activity & Application Knowledge Graph
# ─────────────────────────────────────────────────────────────────────────────
ACTIVITY_ONTOLOGY = {
    "paint": {
        "canonical": "paint",
        "description": "Paint & Graphics Application",
        "binary_win": "mspaint",
        "ubuntu_cmd": "mspaint.exe",
        "keywords": [
            "paint", "painting", "draw", "drawing", "sketch", "sketching", "art",
            "artwork", "illustration", "doodle", "image edit", "mspaint", "canvas",
            "graphics", "picture editor", "draw something", "i want to do painting"
        ],
        "category": "creative"
    },
    "calculator": {
        "canonical": "calculator",
        "description": "Scientific & Standard Calculator",
        "binary_win": "calc",
        "ubuntu_cmd": "calc.exe",
        "keywords": [
            "calc", "calculator", "math", "maths", "arithmetic", "calculate",
            "computation", "compute", "addition", "multiplication", "expenses",
            "budget calculation", "sum", "equation", "solve math", "numbers"
        ],
        "category": "utility"
    },
    "notepad": {
        "canonical": "notepad",
        "description": "Notepad Text Editor",
        "binary_win": "notepad",
        "ubuntu_cmd": "notepad.exe",
        "keywords": [
            "notepad", "notes", "note", "take notes", "write notes", "jot down",
            "text editor", "scratchpad", "memo", "write down", "plain text",
            "edit text", "document", "draft", "todo list"
        ],
        "category": "productivity"
    },
    "brave": {
        "canonical": "brave",
        "description": "Brave Web Browser",
        "binary_win": "brave",
        "ubuntu_cmd": "cmd.exe /c start brave",
        "keywords": ["brave", "brave browser", "brave.exe"],
        "category": "internet"
    },
    "chrome": {
        "canonical": "chrome",
        "description": "Google Chrome Browser",
        "binary_win": "chrome",
        "ubuntu_cmd": "cmd.exe /c start chrome",
        "keywords": ["chrome", "google chrome", "chrome.exe"],
        "category": "internet"
    },
    "edge": {
        "canonical": "edge",
        "description": "Microsoft Edge Browser",
        "binary_win": "msedge",
        "ubuntu_cmd": "cmd.exe /c start msedge",
        "keywords": ["edge", "microsoft edge", "msedge", "msedge.exe"],
        "category": "internet"
    },
    "firefox": {
        "canonical": "firefox",
        "description": "Mozilla Firefox Browser",
        "binary_win": "firefox",
        "ubuntu_cmd": "cmd.exe /c start firefox",
        "keywords": ["firefox", "mozilla", "mozilla firefox"],
        "category": "internet"
    },
    "browser": {
        "canonical": "browser",
        "description": "Web Browser",
        "binary_win": "start https://www.google.com",
        "ubuntu_cmd": "cmd.exe /c start https://www.google.com",
        "keywords": [
            "browser", "web browser", "browse", "browse internet", "surf web",
            "search online", "open website", "internet", "look up online", "surf the web"
        ],
        "category": "internet"
    },
    "terminal": {
        "canonical": "terminal",
        "description": "Interactive Ubuntu WSL2 Terminal",
        "binary_win": "wsl",
        "ubuntu_cmd": "echo 'Ubuntu Terminal Session Active'; uname -a",
        "keywords": [
            "terminal", "console", "bash", "shell", "ubuntu", "wsl", "command prompt",
            "cmd", "powershell", "linux terminal", "cli", "shell session", "bash prompt"
        ],
        "category": "system"
    },
    "htop": {
        "canonical": "htop",
        "description": "Ubuntu Htop Interactive Process Monitor",
        "binary_win": "wsl htop",
        "ubuntu_cmd": "htop",
        "keywords": [
            "htop", "process monitor", "top monitor", "system monitor in terminal",
            "live process tree", "interactive process viewer", "terminal top"
        ],
        "category": "monitoring"
    },
    "taskmgr": {
        "canonical": "task manager",
        "description": "System Task Manager",
        "binary_win": "taskmgr",
        "ubuntu_cmd": "taskmgr.exe",
        "keywords": [
            "taskmgr", "task manager", "kill tasks gui", "view running tasks",
            "performance monitor gui", "resource monitor"
        ],
        "category": "system"
    },
    "explorer": {
        "canonical": "explorer",
        "description": "File Explorer",
        "binary_win": "explorer",
        "ubuntu_cmd": "explorer.exe",
        "keywords": [
            "explorer", "file explorer", "files", "browse files", "open folder",
            "file manager", "directory browser", "my documents", "view files"
        ],
        "category": "system"
    },
    "settings": {
        "canonical": "settings",
        "description": "Windows System Settings",
        "binary_win": "start ms-settings:",
        "ubuntu_cmd": "cmd.exe /c start ms-settings:",
        "keywords": [
            "settings", "control panel", "system preferences", "configure system",
            "system settings", "options", "device settings"
        ],
        "category": "system"
    },
    "vscode": {
        "canonical": "code",
        "description": "Visual Studio Code Editor",
        "binary_win": "code",
        "ubuntu_cmd": "code",
        "keywords": [
            "vscode", "vs code", "code editor", "visual studio code", "programming ide",
            "edit code", "write python", "write javascript", "ide"
        ],
        "category": "development"
    },
    "spotify": {
        "canonical": "spotify",
        "description": "Spotify Music Streaming Player",
        "binary_win": "start spotify:",
        "ubuntu_cmd": "cmd.exe /c start spotify",
        "keywords": [
            "spotify", "music", "listen to music", "play songs", "songs",
            "audio player", "play music", "stream music"
        ],
        "category": "media"
    },
    "vim": {
        "canonical": "vim",
        "description": "Ubuntu Vim Terminal Text Editor",
        "binary_win": "wsl vim",
        "ubuntu_cmd": "vim",
        "keywords": ["vim", "vi editor", "terminal text editor", "vim editor"],
        "category": "development"
    },
    "nano": {
        "canonical": "nano",
        "description": "Ubuntu Nano Terminal Text Editor",
        "binary_win": "wsl nano",
        "ubuntu_cmd": "nano",
        "keywords": ["nano", "nano editor", "simple terminal editor"],
        "category": "development"
    }
}

COMMAND_EXPLANATION_TRIGGERS = [
    r'^(?:what\s+is|what\'s|explain|tell\s+me\s+about|how\s+does|how\s+to\s+use|describe|info\s+on|manual\s+for|man\s+page\s+for|help\s+with|meaning\s+of)\s+([a-zA-Z0-9_\-\.\:\s]+?)(?:\?|$)',
    r'^(?:how\s+do\s+i|how\s+can\s+i)\s+(?:use|run|execute)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\?|$)',
    r'^(?:guide\s+for|syntax\s+of|arguments\s+of|flags\s+of)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\?|$)',
    r'^([a-zA-Z0-9_\-]+)\s+(?:--help|-h|command\s+explanation|manual|explained)$'
]

KNOWN_CLI_COMMANDS = {
    "htop", "top", "grep", "awk", "sed", "chmod", "chown", "tar", "gzip", "zip",
    "unzip", "systemctl", "journalctl", "dmesg", "iptables", "ufw", "curl", "wget",
    "ssh", "scp", "rsync", "find", "locate", "lsof", "netstat", "ss", "ip", "ifconfig",
    "ping", "traceroute", "nslookup", "dig", "df", "du", "free", "uptime", "ps", "kill",
    "pkill", "killall", "docker", "kubectl", "git", "cron", "crontab", "nano", "vim",
    "strace", "perf", "valgrind", "nc", "nmap", "tcpdump", "iostat", "vmstat", "mpstat",
    "ls", "cat", "tail", "head", "less", "more", "sudo", "su", "useradd", "usermod",
    "mount", "umount", "fdisk", "lsblk", "mkfs", "wsl", "powershell", "taskkill", "ipconfig"
}


class NLPEngine:
    """
    Intelligent NLP Intent & Semantic Parsing Engine.
    Employs Ollama (Llama 3.2) as primary zero-shot reasoning layer with granular semantic ontology fallback.
    """

    def classify(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyzes a natural language query:
        1. First tries local Llama 3.2 via Ollama for zero-shot dynamic reasoning.
        2. If Ollama is offline or unavailable, falls back to granular semantic ontology parser.
        """
        raw_query = query.strip()

        # ─── 1. PRIMARY LAYER: OLLAMA / LLAMA 3.2 LOCAL REASONING ─────────────
        try:
            llm_result = ollama_engine.reason_and_classify(raw_query, context)
            if llm_result and "intent" in llm_result:
                target = llm_result.get("target_app_or_command", "")
                intent = llm_result.get("intent", "GENERAL_QUERY")

                return {
                    "intent": intent,
                    "target_app": target if intent == "APPLICATION_LAUNCH" else None,
                    "target_command": target if intent in ["COMMAND_EXPLANATION", "SYSTEM_COMMAND_EXECUTION"] else None,
                    "confidence": float(llm_result.get("confidence", 0.95)),
                    "reasoning": llm_result.get("reasoning", "Llama 3.2 zero-shot semantic reasoning."),
                    "response_markdown": llm_result.get("response_markdown"),
                    "proposed_commands": llm_result.get("proposed_commands", []),
                    "recommendations": llm_result.get("recommendations", []),
                    "is_gui_app": llm_result.get("is_gui_app", False),
                    "llm_engine": llm_result.get("llm_engine", "ollama/llama3.2"),
                    "entities": {"query": raw_query, "target": target}
                }
        except Exception as e:
            logger.debug(f"Ollama reasoning fallback: {e}")

        # ─── 2. FALLBACK LAYER: LOCAL GRANULAR SEMANTIC PARSER ────────────────
        return self._classify_semantic_fallback(raw_query)

    def _classify_semantic_fallback(self, raw_query: str) -> Dict[str, Any]:
        """Local granular semantic analyzer used when Ollama daemon is offline."""
        q_lower = raw_query.lower()

        # 1. Command Explanation / Knowledge
        expl_intent = self._check_command_explanation(raw_query, q_lower)
        if expl_intent:
            return expl_intent

        # 2. System Command / Task Execution (e.g. "how to find large files", "open ports")
        cmd_intent = self._check_command_execution_intent(raw_query, q_lower)
        if cmd_intent:
            return cmd_intent

        # 3. Dynamic Application & Activity Launch (e.g. "open brave", "i want to do painting")
        app_intent = self._check_application_intent(raw_query, q_lower)
        if app_intent:
            return app_intent

        # 4. Process Management
        proc_intent = self._check_process_intent(raw_query, q_lower)
        if proc_intent:
            return proc_intent

        # 5. Network Diagnostics
        net_intent = self._check_network_intent(raw_query, q_lower)
        if net_intent:
            return net_intent

        # 6. Storage & Disk
        stor_intent = self._check_storage_intent(raw_query, q_lower)
        if stor_intent:
            return stor_intent

        # 7. Log Analysis
        log_intent = self._check_log_intent(raw_query, q_lower)
        if log_intent:
            return log_intent

        # 8. CPU & RAM Performance
        perf_intent = self._check_performance_intent(raw_query, q_lower)
        if perf_intent:
            return perf_intent

        # 9. Holistic Diagnosis Fallback
        return {
            "intent": "SYSTEM_DIAGNOSIS",
            "target_app": None,
            "target_command": None,
            "confidence": 0.88,
            "reasoning": "Semantic analyzer classified as holistic system telemetry & bottleneck scan.",
            "llm_engine": "semantic_nlp",
            "entities": {"query": raw_query}
        }

    def _check_command_explanation(self, query: str, q_lower: str) -> Optional[Dict[str, Any]]:
        for pattern in COMMAND_EXPLANATION_TRIGGERS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                cmd_candidate = match.group(1).strip().lower()
                cmd_candidate = re.sub(r'[\?\,\.\!]+$', '', cmd_candidate).strip()
                tokens = cmd_candidate.split()
                primary_cmd = tokens[0] if tokens else cmd_candidate

                if any(w in cmd_candidate for w in ["laptop slow", "system slow", "computer slow", "wifi not working", "internet down"]):
                    return None

                return {
                    "intent": "COMMAND_EXPLANATION",
                    "target_command": primary_cmd,
                    "full_target": cmd_candidate,
                    "target_app": None,
                    "confidence": 0.96,
                    "reasoning": f"Inquiring about syntax, options, and operational usage of command '{primary_cmd}'.",
                    "llm_engine": "semantic_nlp",
                    "entities": {"command": primary_cmd, "query_phrase": cmd_candidate}
                }

        tokens = [t.strip(",.?! ") for t in q_lower.split()]
        if len(tokens) == 1 and tokens[0] in KNOWN_CLI_COMMANDS:
            return {
                "intent": "COMMAND_EXPLANATION",
                "target_command": tokens[0],
                "full_target": tokens[0],
                "target_app": None,
                "confidence": 0.92,
                "reasoning": f"Matched system utility '{tokens[0]}'.",
                "llm_engine": "semantic_nlp",
                "entities": {"command": tokens[0]}
            }

        if len(tokens) == 2 and tokens[0] in ["man", "info", "help"] and tokens[1] in KNOWN_CLI_COMMANDS:
            return {
                "intent": "COMMAND_EXPLANATION",
                "target_command": tokens[1],
                "full_target": tokens[1],
                "target_app": None,
                "confidence": 0.98,
                "reasoning": f"Manual query for command '{tokens[1]}'.",
                "llm_engine": "semantic_nlp",
                "entities": {"command": tokens[1]}
            }
        return None

    def _check_application_intent(self, query: str, q_lower: str) -> Optional[Dict[str, Any]]:
        # 1. Direct verb-object extraction (e.g., "open brave", "launch chrome", "start notepad")
        verb_match = re.match(
            r'^(?:please\s+)?(?:i\s+(?:want|need|would\s+like)\s+to\s+)?(?:open|launch|start|run|spawn|fire\s+up|execute)\s+(?:the\s+)?([a-zA-Z0-9_\-\.\s]+)$',
            q_lower,
            re.IGNORECASE
        )
        if verb_match:
            extracted_target = verb_match.group(1).strip()
            non_app_terms = ["system diagnosis", "telemetry", "ml anomaly", "diagnostic", "full scan", "audit", "ports", "large files"]
            if not any(term in extracted_target for term in non_app_terms):
                # Check ontology for canonical name
                canonical_app = extracted_target
                app_desc = extracted_target
                if extracted_target in ACTIVITY_ONTOLOGY:
                    canonical_app = ACTIVITY_ONTOLOGY[extracted_target]["canonical"]
                    app_desc = ACTIVITY_ONTOLOGY[extracted_target]["description"]
                else:
                    for k, data in ACTIVITY_ONTOLOGY.items():
                        if extracted_target in data["keywords"]:
                            canonical_app = data["canonical"]
                            app_desc = data["description"]
                            break

                return {
                    "intent": "APPLICATION_LAUNCH",
                    "target_app": canonical_app,
                    "confidence": 0.98,
                    "reasoning": f"Direct request to launch application '{canonical_app}'.",
                    "llm_engine": "semantic_nlp",
                    "entities": {"target_app": canonical_app, "description": app_desc}
                }

        # 2. Activity / Goal Matching
        best_match_app = None
        best_score = 0
        matching_keyword = ""

        for app_key, app_data in ACTIVITY_ONTOLOGY.items():
            for kw in app_data["keywords"]:
                if kw in q_lower:
                    score = len(kw) * 2
                    if q_lower.startswith("i want to ") or q_lower.startswith("i need to ") or q_lower.startswith("let's "):
                        score += 25
                    if score > best_score:
                        best_score = score
                        best_match_app = app_data
                        matching_keyword = kw

        if best_match_app and best_score >= 8:
            return {
                "intent": "APPLICATION_LAUNCH",
                "target_app": best_match_app["canonical"],
                "confidence": min(0.99, 0.85 + (best_score / 100.0)),
                "reasoning": f"Semantic NLP identified activity '{matching_keyword}' mapped to '{best_match_app['description']}'.",
                "llm_engine": "semantic_nlp",
                "entities": {
                    "activity": matching_keyword,
                    "target_app": best_match_app["canonical"],
                    "description": best_match_app["description"]
                }
            }

        return None

    def _check_command_execution_intent(self, query: str, q_lower: str) -> Optional[Dict[str, Any]]:
        task_indicators = [
            "how to find large files", "find large files", "find largest files",
            "show open ports", "check open ports", "list listening ports",
            "backup documents", "archive folder", "compress files",
            "update packages", "upgrade system", "system uptime"
        ]
        if any(ind in q_lower for ind in task_indicators):
            return {
                "intent": "SYSTEM_COMMAND_EXECUTION",
                "confidence": 0.95,
                "reasoning": f"Identified administrative task intent from query: '{query}'.",
                "llm_engine": "semantic_nlp",
                "entities": {"task_query": query}
            }
        return None

    def _check_process_intent(self, query: str, q_lower: str) -> Optional[Dict[str, Any]]:
        kill_match = re.search(r'(?:kill|terminate|stop|force\s+close)\s+(?:process\s+|task\s+|pid\s+)?([a-zA-Z0-9_\-\.]+)', q_lower)
        if kill_match:
            target = kill_match.group(1).strip()
            is_pid = target.isdigit()
            return {
                "intent": "PROCESS_ANALYSIS",
                "action": "kill",
                "target": target,
                "is_pid": is_pid,
                "confidence": 0.97,
                "reasoning": f"Detected process termination intent for {'PID' if is_pid else 'process'} '{target}'.",
                "llm_engine": "semantic_nlp",
                "entities": {"target": target, "is_pid": is_pid}
            }

        if any(w in q_lower for w in ["processes", "process tree", "top process", "zombie process", "hung process", "heavy process", "memory hog", "cpu hog"]):
            return {
                "intent": "PROCESS_ANALYSIS",
                "action": "inspect",
                "confidence": 0.95,
                "reasoning": "Detected request to inspect active system tasks.",
                "llm_engine": "semantic_nlp",
                "entities": {}
            }
        return None

    def _check_network_intent(self, query: str, q_lower: str) -> Optional[Dict[str, Any]]:
        if any(w in q_lower for w in ["network", "wifi", "internet", "ping", "dns", "packet loss", "ip address", "gateway", "firewall", "bandwidth", "speed test"]):
            return {
                "intent": "NETWORK_DIAGNOSIS",
                "confidence": 0.95,
                "reasoning": "User requested network interfaces, DNS, or connectivity diagnostics.",
                "llm_engine": "semantic_nlp",
                "entities": {"topic": "network"}
            }
        return None

    def _check_storage_intent(self, query: str, q_lower: str) -> Optional[Dict[str, Any]]:
        if any(w in q_lower for w in ["disk", "storage", "space", "partition", "drive", "free up space", "clean cache", "disk full", "filesystem", "du -h", "df -h"]):
            return {
                "intent": "STORAGE_OPTIMIZATION",
                "confidence": 0.95,
                "reasoning": "User requested storage volume inspection or cleanup.",
                "llm_engine": "semantic_nlp",
                "entities": {"topic": "storage"}
            }
        return None

    def _check_log_intent(self, query: str, q_lower: str) -> Optional[Dict[str, Any]]:
        if any(w in q_lower for w in ["logs", "log files", "dmesg", "journalctl", "syslog", "kernel panic", "error events", "crash report", "system errors"]):
            return {
                "intent": "LOG_ANALYSIS",
                "confidence": 0.95,
                "reasoning": "User requested analysis of system logs or error events.",
                "llm_engine": "semantic_nlp",
                "entities": {"topic": "logs"}
            }
        return None

    def _check_performance_intent(self, query: str, q_lower: str) -> Optional[Dict[str, Any]]:
        if any(w in q_lower for w in ["cpu", "processor load", "throttling", "core usage"]):
            return {
                "intent": "CPU_DIAGNOSIS",
                "confidence": 0.95,
                "reasoning": "User requested CPU workload analysis.",
                "llm_engine": "semantic_nlp",
                "entities": {"resource": "cpu"}
            }
        if any(w in q_lower for w in ["ram", "memory", "swap", "out of memory", "oom", "memory leak"]):
            return {
                "intent": "MEMORY_DIAGNOSIS",
                "confidence": 0.95,
                "reasoning": "User requested RAM and swap memory analysis.",
                "llm_engine": "semantic_nlp",
                "entities": {"resource": "memory"}
            }
        if any(w in q_lower for w in ["slow", "lag", "freezing", "stutter", "why is my laptop", "health check", "diagnose", "system status"]):
            return {
                "intent": "SYSTEM_DIAGNOSIS",
                "confidence": 0.95,
                "reasoning": "User requested holistic multi-variate system health diagnosis.",
                "llm_engine": "semantic_nlp",
                "entities": {"general": True}
            }
        return None


nlp_engine = NLPEngine()
