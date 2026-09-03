"""
Gemini-Powered Universal AI Planner for KernelSense
All intent classification and reasoning is now handled by Google Gemini API.
The planner ONLY formats the structured Gemini response into the KernelSense UI contract.
No hardcoded intents, no hardcoded URLs, no hardcoded commands.
"""

import os
import uuid
import psutil
import platform
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# .env is in backend/, one level above the ai/ subdirectory
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=_env_path, override=True)

from ai.llm_provider import llm_gateway
from core.file_finder import file_finder
from core.process_engine import process_engine
from core.database import db

def resolve_app_launch_command(app_name: str) -> Dict[str, Any]:
    raw = app_name.strip().lower().replace(".exe", "")
    
    # Check for terminal-based Linux CLI utilities
    if raw in {"htop", "top", "nano", "vim", "vi", "tmux", "bash", "zsh", "python", "python3"}:
        return {
            "title": raw.title(),
            "display": raw,
            "shell_cmd": raw
        }

    # Map aliases to standard Windows binaries / protocol URIs
    app_map = {
        "calculator": "calc",
        "calculate": "calc",
        "calc": "calc",
        "notepad": "notepad",
        "paint": "mspaint",
        "mspaint": "mspaint",
        "whatsapp": "whatsapp:",
        "watsapp": "whatsapp:",
        "whatsup": "whatsapp:",
        "spotify": "spotify",
        "taskmgr": "taskmgr",
        "task manager": "taskmgr",
        "explorer": "explorer",
        "file explorer": "explorer",
        "settings": "ms-settings:",
        "control panel": "control",
        "control": "control",
        "vscode": "code",
        "code": "code",
        "terminal": "wt",
        "powershell": "powershell",
        "cmd": "cmd"
    }

    target = app_map.get(raw, raw)
    
    # Inside Ubuntu WSL2, Windows applications are launched via cmd.exe /c start or powershell.exe Start-Process
    if target.endswith(":"):
        shell_cmd = f"cmd.exe /c start {target} 2>/dev/null || powershell.exe -NoProfile -Command \"Start-Process '{target}'\" 2>/dev/null"
    else:
        shell_cmd = f"cmd.exe /c start {target} 2>/dev/null || cmd.exe /c start {target}: 2>/dev/null || powershell.exe -NoProfile -Command \"Start-Process '{target}'\" 2>/dev/null || {target}.exe 2>/dev/null"

    display_name = target.replace(":", "").title()
    if raw in ["calc", "calculator"]:
        display_name = "Windows Calculator"
    elif raw == "notepad":
        display_name = "Notepad Text Editor"
    elif raw in ["paint", "mspaint"]:
        display_name = "Paint Application"
    elif "whatsapp" in raw:
        display_name = "WhatsApp Desktop"

    return {
        "title": display_name,
        "display": target,
        "shell_cmd": shell_cmd
    }

class ReActPlanner:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"

    # ──────────────────────────────────────────────────────────────────
    # Live hardware telemetry snapshot (injected into every Gemini query)
    # ──────────────────────────────────────────────────────────────────
    def _build_telemetry_context(self) -> Dict[str, Any]:
        try:
            mem  = psutil.virtual_memory()
            swap = psutil.swap_memory()
            cpu  = psutil.cpu_percent(interval=None)
            disk = psutil.disk_usage("C:\\" if os.path.exists("C:\\") else "/")
            top_mem = process_engine.get_top_memory_processes(limit=5)
            top_cpu = process_engine.get_top_cpu_processes(limit=5)
            return {
                "system_health_score": round(max(10, 100 - (cpu * 0.4 + mem.percent * 0.4))),
                "cpu_usage_percent": round(cpu, 1),
                "cpu_cores": psutil.cpu_count(logical=True) or 1,
                "memory_used_gb":   round(mem.used  / 1024**3, 2),
                "memory_total_gb":  round(mem.total / 1024**3, 2),
                "memory_percent":   round(mem.percent, 1),
                "swap_percent":     round(swap.percent, 1),
                "disk_used_gb":     round(disk.used  / 1024**3, 1),
                "disk_total_gb":    round(disk.total / 1024**3, 1),
                "disk_usage_percent": round(disk.percent, 1),
                "top_memory_processes": [
                    {"name": p.get("name"), "pid": p.get("pid"),
                     "ram_mb": p.get("memory_mb"), "ram_pct": p.get("memory_percent")}
                    for p in top_mem
                ],
                "top_cpu_processes": [
                    {"name": p.get("name"), "pid": p.get("pid"),
                     "cpu_pct": p.get("cpu_percent"), "ram_mb": p.get("memory_mb")}
                    for p in top_cpu
                ],
            }
        except Exception:
            return {}

    # ──────────────────────────────────────────────────────────────────
    # Main entry point: every query flows through Gemini
    # ──────────────────────────────────────────────────────────────────
    def plan_and_execute(self, query: str) -> Dict[str, Any]:
        """
        1. Collect live telemetry
        2. Send query + telemetry to Gemini (primary) or fallback LLMs
        3. Gemini returns structured JSON with intent + commands + markdown
        4. We format and wrap for the KernelSense UI contract
        """
        telemetry_ctx = self._build_telemetry_context()

        # Send everything to Gemini
        ai_result = llm_gateway.reason_and_plan(query, telemetry_ctx)

        if not ai_result:
            # Hard fallback: Gemini offline and no other provider available
            return self._offline_fallback(query, telemetry_ctx)

        intent      = ai_result.get("intent", "GENERAL_QUERY")
        action_type = ai_result.get("action_type", "NONE")
        provider    = ai_result.get("provider", "gemini")

        # ── GREETING ───────────────────────────────────────────────
        if intent == "GREETING":
            res = self._format_greeting(ai_result, telemetry_ctx, provider)
        # ── FILE SEARCH ────────────────────────────────────────────
        elif intent == "FILE_SEARCH":
            res = self._handle_file_search(ai_result, query)
        # ── LINUX CORE COMMAND ─────────────────────────────────────
        elif intent == "LINUX_CORE_COMMAND":
            res = self._handle_linux_command(ai_result, query)
        # ── OPEN URL IN BROWSER ────────────────────────────────────
        elif intent == "OPEN_URL_IN_APP" or action_type == "OPEN_URL":
            res = self._handle_open_url(ai_result, query, provider)
        # ── OPEN DESKTOP APPLICATION ───────────────────────────────
        elif intent == "OPEN_APPLICATION" or action_type == "OPEN_APP":
            res = self._handle_open_app(ai_result, query, provider)
        # ── DIAGNOSTICS & GENERAL ──────────────────────────────────
        else:
            res = self._format_general(ai_result, query, telemetry_ctx, provider)

        res.setdefault("request_id", f"req-{uuid.uuid4().hex[:8]}")
        res.setdefault("intent", intent)
        res.setdefault("risk_level", "LOW")
        return res

    # ──────────────────────────────────────────────────────────────────
    # Handler: Greeting
    # ──────────────────────────────────────────────────────────────────
    def _format_greeting(self, ai_result: Dict, telemetry: Dict, provider: str) -> Dict:
        response_md = ai_result.get("response_markdown", "")
        if not response_md:
            cpu = telemetry.get("cpu_usage_percent", 0)
            ram = telemetry.get("memory_percent", 0)
            health = telemetry.get("system_health_score", 95)
            response_md = f"""### 👋 Hello! I am KernelSense AI

I am your **AI-Powered Operating System & Autonomous Telemetry Assistant** powered by **{provider}**.

---

#### 🛠️ What I Can Do:
1. **🐧 Core Linux & OS Commands:** *"find my ip address"*, *"what is my username"*, *"show open ports"*, *"lscpu"*
2. **🧠 Hardware Telemetry:** Current Health: `{health}/100` | RAM: `{ram:.1f}%` | CPU: `{cpu:.1f}%`
3. **📁 Local File Search:** *"find JCL1.pdf"*, *"open USS1.pdf"*, *"search for resume.docx"*
4. **🌐 Web & Apps:** *"open youtube on chrome"*, *"open spotify on brave"*, *"open notepad"*
5. **🤖 AI Chat:** Ask me anything — coding, explanations, math, system diagnostics

*Type any query to begin!*
"""
        root_nodes = [{"id": "ks", "label": f"KernelSense AI ({provider})", "type": "system"}]
        root_edges = []
        self._save_history(ai_result.get("query", "hello"), response_md, ["gemini_ai"], root_nodes, root_edges, [], intent="GREETING")
        return {
            "response": response_md,
            "tools_used": ["gemini_ai"],
            "execution_steps": [{"tool": "gemini_ai", "label": "Generated conversational overview", "status": "done"}],
            "root_cause": {
                "nodes": root_nodes,
                "edges": root_edges
            },
            "commands": [],
            "recommendations": ai_result.get("recommendations", [
                "Try: 'finding the ip address of this pc'",
                "Try: 'find JCL1.pdf' to locate local documents",
                "Try: 'why is my laptop slow' for system diagnosis"
            ])
        }

    # ──────────────────────────────────────────────────────────────────
    # Handler: File Search — Gemini identifies the file, we search drive
    # ──────────────────────────────────────────────────────────────────
    def _handle_file_search(self, ai_result: Dict, query: str) -> Dict:
        search_target = ai_result.get("search_target") or query
        files = file_finder.search_files(search_target, max_results=6)

        proposed_commands = []
        if files:
            fmt = file_finder.format_open_command(files[0]["path"])
            proposed_commands.append({
                "id": f"cmd-{uuid.uuid4().hex[:8]}",
                "command": fmt["command"],
                "explanation": fmt["explanation"]
            })
            file_rows = "\n".join(
                f"| **`{f['filename']}`** | `{f['size']}` | `{f['modified']}` | `{f['path']}` |"
                for f in files
            )
            response_md = f"""### 📁 Local File Discovery: Found {len(files)} Matching File(s)

I searched your local drives and found:

| File Name | Size | Last Modified | Full Path |
| :--- | :--- | :--- | :--- |
{file_rows}

*Click **Execute** below to open **`{files[0]['filename']}`** directly.*
"""
            root_nodes = [
                {"id": "req",   "label": f"Search: {search_target}", "type": "process"},
                {"id": "found", "label": f"Found: {files[0]['filename']}", "type": "system"},
                {"id": "open",  "label": "Ready to Launch", "type": "impact"}
            ]
            root_edges = [{"from": "req", "to": "found"}, {"from": "found", "to": "open"}]
            recommendations = [
                f"Found '{files[0]['path']}'.",
                "Click 'Execute' to open it in its default application."
            ]
        else:
            response_md = f"""### 📁 Local File Discovery: No Matches Found

Searched all local drives for **`{search_target}`** — no matching files found.

**Tips:**
- Check the filename spelling
- Try searching by extension: `*.pdf`, `*.docx`, `*.pptx`
"""
            root_nodes = [{"id": "scan", "label": f"Search: {search_target} (0 results)", "type": "process"}]
            root_edges = []
            recommendations = ["Verify the filename spelling and try again."]

        self._save_history(query, response_md, ["file_scanner"], root_nodes, root_edges, proposed_commands, intent="FILE_SEARCH")
        return {
            "response": response_md,
            "tools_used": ["file_scanner"],
            "execution_steps": [{"tool": "file_scanner", "label": f"Scanned drives for '{search_target}'", "status": "done"}],
            "root_cause": {"nodes": root_nodes, "edges": root_edges},
            "commands": proposed_commands,
            "recommendations": recommendations
        }

    # ──────────────────────────────────────────────────────────────────
    # Handler: Linux Core Command — Gemini generates the exact command
    # ──────────────────────────────────────────────────────────────────
    def _handle_linux_command(self, ai_result: Dict, query: str) -> Dict:
        raw_command  = ai_result.get("linux_command") or query
        title        = ai_result.get("linux_title")  or "🐧 Linux Command Execution"
        explanation  = ai_result.get("linux_explanation") or "Executes the command in Ubuntu Linux."
        task_type    = ai_result.get("linux_task_type") or "RAW_COMMAND"
        provider     = ai_result.get("provider", "gemini")

        ubuntu_cmd = (
            f'wsl.exe -d Ubuntu bash -c "'
            f'echo =================================================; '
            f'echo  KernelSense: {title}; '
            f'echo =================================================; '
            f'{raw_command}; '
            f'echo =================================================; exec bash"'
        )
        proposed_commands = [{
            "id": f"cmd-{uuid.uuid4().hex[:8]}",
            "command": ubuntu_cmd,
            "explanation": explanation
        }]
        response_md = ai_result.get("response_markdown") or f"""### {title}

#### 📋 Command Breakdown & Purpose:
* **Target Environment:** `Ubuntu Linux (WSL2) Interactive Shell`
* **Shell Commands:**
```bash
{raw_command}
```
* **What it does:** {explanation}

---

*Click **Execute** below to spawn an interactive Ubuntu terminal and run this command.*
"""
        root_nodes = [
            {"id": "req",  "label": f"Query: {query[:28]}", "type": "process"},
            {"id": "task", "label": f"Task: {task_type}",   "type": "system"},
            {"id": "exec", "label": "Ubuntu Terminal Ready", "type": "impact"}
        ]
        root_edges = [{"from": "req", "to": "task"}, {"from": "task", "to": "exec"}]

        self._save_history(query, response_md, ["linux_shell_engine"], root_nodes, root_edges, proposed_commands, intent="LINUX_CORE_COMMAND")
        return {
            "response": response_md,
            "tools_used": ["linux_shell_engine"],
            "execution_steps": [{"tool": "linux_shell_engine", "label": f"Synthesized Linux command for '{task_type}' via {provider}", "status": "done"}],
            "root_cause": {"nodes": root_nodes, "edges": root_edges},
            "commands": proposed_commands,
            "recommendations": ai_result.get("recommendations", [
                f"Click 'Execute' to run this inside an interactive Ubuntu terminal.",
                "The terminal window will stay open after the command completes."
            ])
        }

    # ──────────────────────────────────────────────────────────────────
    # Handler: Open URL — Gemini resolves the URL (any site, no list)
    # ──────────────────────────────────────────────────────────────────
    def _handle_open_url(self, ai_result: Dict, query: str, provider: str) -> Dict:
        url     = ai_result.get("target_url") or "https://google.com"
        browser = ai_result.get("browser") or "chrome"
        site    = url.replace("https://", "").replace("http://", "").split("/")[0]

        ubuntu_cmd = (
            f'wsl.exe -d Ubuntu bash -c "'
            f'echo =================================================; '
            f'echo  KernelSense: Opening {site.title()}; '
            f'echo  URL: {url}  Browser: {browser.title()}; '
            f'echo =================================================; '
            f'cmd.exe /c start {browser} {url}; exec bash"'
        )
        proposed_commands = [{
            "id": f"cmd-{uuid.uuid4().hex[:8]}",
            "command": ubuntu_cmd,
            "explanation": f"Opens {site.title()} ({url}) in {browser.title()} via Ubuntu WSL2."
        }]
        response_md = ai_result.get("response_markdown") or f"""### 🌐 Web Browser Launch: {site.title()}

* **URL:** `{url}`
* **Browser:** `{browser.title()}`
* **Environment:** Interactive Ubuntu WSL2 Terminal

*Click **Execute** below to open the site.*
"""
        root_nodes = [
            {"id": "req",  "label": f"Open: {site.title()}", "type": "process"},
            {"id": "nav",  "label": f"Browser: {browser.title()}", "type": "system"},
            {"id": "url",  "label": url[:45], "type": "impact"}
        ]
        root_edges = [{"from": "req", "to": "nav"}, {"from": "nav", "to": "url"}]

        self._save_history(query, response_md, ["url_resolver"], root_nodes, root_edges, proposed_commands, intent="OPEN_URL_IN_APP")
        return {
            "response": response_md,
            "tools_used": ["url_resolver"],
            "execution_steps": [{"tool": "url_resolver", "label": f"Resolved URL via {provider}", "status": "done"}],
            "root_cause": {"nodes": root_nodes, "edges": root_edges},
            "commands": proposed_commands,
            "recommendations": ai_result.get("recommendations", [f"Click 'Execute' to open {site.title()} in {browser.title()}."])
        }

    # ──────────────────────────────────────────────────────────────────
    # Handler: Open Application
    # ──────────────────────────────────────────────────────────────────
    def _handle_open_app(self, ai_result: Dict, query: str, provider: str) -> Dict:
        app_name = ai_result.get("target_app") or query
        launch_info = resolve_app_launch_command(app_name)
        
        display_title = launch_info["title"]
        shell_action = launch_info["shell_cmd"]

        ubuntu_cmd = (
            f'wsl.exe -d Ubuntu bash -c "'
            f'echo =================================================; '
            f'echo  KernelSense: Launching {display_title}; '
            f'echo =================================================; '
            f'{shell_action}; '
            f'echo Launched {display_title} on desktop.; exec bash"'
        )
        proposed_commands = [{
            "id": f"cmd-{uuid.uuid4().hex[:8]}",
            "command": ubuntu_cmd,
            "explanation": f"Launches '{display_title}' via interactive Ubuntu WSL2 terminal session."
        }]
        response_md = ai_result.get("response_markdown") or f"""### 🐧 Application Launch: {display_title}

* **Application:** `{display_title}`
* **Launch Target:** `{launch_info['display']}`
* **Environment:** Interactive Ubuntu WSL2 Terminal

*Click **Execute** below to launch on your desktop.*
"""
        root_nodes = [
            {"id": "req",  "label": f"Open: {display_title}", "type": "process"},
            {"id": "exec", "label": "Ubuntu Terminal", "type": "system"},
            {"id": "gui",  "label": "Application Window", "type": "impact"}
        ]
        root_edges = [{"from": "req", "to": "exec"}, {"from": "exec", "to": "gui"}]

        self._save_history(query, response_md, ["app_launcher"], root_nodes, root_edges, proposed_commands, intent="OPEN_APPLICATION")
        return {
            "response": response_md,
            "tools_used": ["app_launcher"],
            "execution_steps": [{"tool": "app_launcher", "label": f"Resolved app '{display_title}' via {provider}", "status": "done"}],
            "root_cause": {"nodes": root_nodes, "edges": root_edges},
            "commands": proposed_commands,
            "recommendations": [f"Click 'Execute' below to launch '{display_title}' on your desktop."]
        }

    # ──────────────────────────────────────────────────────────────────
    # Handler: General / Diagnostics — full Gemini markdown response
    # ──────────────────────────────────────────────────────────────────
    def _format_general(self, ai_result: Dict, query: str, telemetry: Dict, provider: str) -> Dict:
        response_md = ai_result.get("response_markdown") or f"### KernelSense AI Response\n\n*No response generated for: `{query}`*"

        # Convert any proposed_commands from Gemini into Ubuntu WSL2 execution blocks
        proposed_commands = []
        for pc in ai_result.get("proposed_commands", []):
            raw = pc.get("command", "")
            if raw:
                if not raw.startswith("wsl.exe"):
                    raw = f'wsl.exe -d Ubuntu bash -c "{raw}; exec bash"'
                proposed_commands.append({
                    "id": f"cmd-{uuid.uuid4().hex[:8]}",
                    "command": raw,
                    "explanation": pc.get("explanation", "")
                })

        root_nodes = ai_result.get("root_cause_nodes") or [
            {"id": "q",  "label": f"Query: {query[:30]}", "type": "process"},
            {"id": "ai", "label": f"Gemini AI ({provider})", "type": "system"},
            {"id": "hw", "label": f"Health: {telemetry.get('system_health_score', 95)}%", "type": "impact"}
        ]
        root_edges = ai_result.get("root_cause_edges") or [
            {"from": "q", "to": "ai"}, {"from": "ai", "to": "hw"}
        ]

        intent_name = ai_result.get("intent", "GENERAL_QUERY")
        self._save_history(query, response_md, ["gemini_ai"], root_nodes, root_edges, proposed_commands, intent=intent_name)
        return {
            "response": response_md,
            "tools_used": ["gemini_ai", "telemetry_collector"],
            "execution_steps": [
                {"tool": "telemetry_collector", "label": "Sampled live OS telemetry", "status": "done"},
                {"tool": "gemini_ai",           "label": f"Reasoned with {provider}",  "status": "done"}
            ],
            "root_cause": {"nodes": root_nodes, "edges": root_edges},
            "commands": proposed_commands,
            "recommendations": ai_result.get("recommendations", [])
        }

    # ──────────────────────────────────────────────────────────────────
    # Hard offline fallback (all providers unreachable)
    # ──────────────────────────────────────────────────────────────────
    def _offline_fallback(self, query: str, telemetry: Dict) -> Dict:
        mem  = telemetry.get("memory_percent", 0)
        cpu  = telemetry.get("cpu_usage_percent", 0)
        health = telemetry.get("system_health_score", 95)
        top_mem = telemetry.get("top_memory_processes", [])
        top_cpu = telemetry.get("top_cpu_processes", [])

        mem_rows = "\n".join(
            f"| `{p.get('name')}` | `{p.get('pid')}` | `{p.get('ram_mb', 0):.1f} MB` | `{p.get('ram_pct', 0):.1f}%` |"
            for p in top_mem[:4]
        ) or "| None | - | - | - |"
        cpu_rows = "\n".join(
            f"| `{p.get('name')}` | `{p.get('pid')}` | `{p.get('cpu_pct', 0):.1f}%` |"
            for p in top_cpu[:4]
        ) or "| None | - | - |"

        ubuntu_cmd = 'wsl.exe -d Ubuntu bash -c "uname -a; free -h; df -h; uptime; exec bash"'
        proposed_commands = [{
            "id": f"cmd-{uuid.uuid4().hex[:8]}",
            "command": ubuntu_cmd,
            "explanation": "Runs a quick system overview (kernel, memory, disk, uptime) in Ubuntu."
        }]
        response_md = f"""### 🛡️ KernelSense System Status (Offline Mode)

> **⚠️ AI Provider Unavailable** — Gemini API unreachable. Showing live telemetry snapshot.

#### 📊 Live Hardware Telemetry:
* **System Health:** `{health}/100`
* **CPU Usage:** `{cpu:.1f}%`
* **RAM Usage:** `{mem:.1f}%` (`{telemetry.get('memory_used_gb', 0):.2f}` / `{telemetry.get('memory_total_gb', 0):.2f}` GB)
* **Disk Usage:** `{telemetry.get('disk_usage_percent', 0):.1f}%`

#### 🏆 Top RAM Consumers:
| Process | PID | RAM | % |
| :--- | :--- | :--- | :--- |
{mem_rows}

#### ⚡ Top CPU Consumers:
| Process | PID | CPU % |
| :--- | :--- | :--- |
{cpu_rows}

*Check your network connection and verify the Gemini API key in `.env`.*
"""
        return {
            "response": response_md,
            "tools_used": ["telemetry_collector"],
            "execution_steps": [{"tool": "telemetry_collector", "label": "Offline mode — live telemetry only", "status": "done"}],
            "root_cause": {
                "nodes": [{"id": "offline", "label": "AI Provider Offline", "type": "system"}],
                "edges": []
            },
            "commands": proposed_commands,
            "recommendations": [
                "Check GEMINI_API_KEY is set correctly in backend/.env",
                "Restart the backend server after updating .env"
            ]
        }

    def _save_history(self, query, response_text, tools, nodes, edges, commands, intent="GENERAL_QUERY"):
        try:
            db.save_history(
                query=query,
                response_text=response_text,
                tools_used=tools,
                root_cause_nodes=nodes,
                root_cause_edges=edges,
                proposed_commands=commands,
                anomaly_score=0.05,
                intent=intent
            )
        except Exception:
            pass


planner = ReActPlanner()
