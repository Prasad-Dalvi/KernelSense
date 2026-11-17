"""
Gemini-Powered Universal AI Planner for KernelSense
All intent classification and reasoning is now handled by Google Gemini API.
The planner ONLY formats the structured Gemini response into the KernelSense UI contract.
No hardcoded intents, no hardcoded URLs, no hardcoded commands.
"""

import os
import re
import uuid
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# .env is in backend/, one level above the ai/ subdirectory
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=_env_path, override=True)

from ai.llm_provider import llm_gateway
from core.directory_operations import list_directory_files, parse_directory_listing_request
from core.file_finder import file_finder
from core.file_operations import parse_file_creation_request, validate_file_target
from core.process_engine import process_engine
from core.command_safety import command_safety_engine
from core.database import db
from core.live_telemetry import telemetry_collector


def format_metric(value: Any, digits: int = 1, suffix: str = "") -> str:
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}{suffix}"
    return "Unavailable"


def resolve_app_launch_command(app_name: str) -> Dict[str, Any]:
    raw = app_name.strip().lower().replace(".exe", "")
    
    # Check for terminal-based Linux CLI utilities
    if raw in {"htop", "top", "nano", "vim", "vi", "tmux", "bash", "zsh", "python", "python3"}:
        return {
            "title": raw.title(),
            "display": raw,
            "shell_cmd": raw
        }

    from windows.apps import resolve_app_launch_command as win_resolve
    return win_resolve(app_name)

class ReActPlanner:
    # ──────────────────────────────────────────────────────────────────
    # Live hardware telemetry snapshot (injected into every Gemini query)
    # ──────────────────────────────────────────────────────────────────
    def _build_telemetry_context(self) -> Dict[str, Any]:
        stats = telemetry_collector.get_all_stats()
        host = telemetry_collector.get_host_info()
        mem = stats["memory"]
        disk = stats["storage"]
        return {
            "host": {
                key: host.get(key)
                for key in (
                    "os_name",
                    "os_release",
                    "os_version",
                    "processor",
                    "logical_cores",
                    "physical_cores",
                    "cpu_frequency_mhz",
                )
            },
            "system_health_score": stats["health"]["score"],
            "cpu_usage_percent": stats["cpu"]["cpu_usage"],
            "cpu_cores": stats["cpu"]["cpu_count"],
            "memory_used_gb": mem["used_gb"],
            "memory_total_gb": mem["total_gb"],
            "memory_percent": mem["memory_percent"],
            "swap_percent": mem["swap_percent"],
            "swap_used_gb": mem["swap_used_gb"],
            "swap_total_gb": mem["swap_total_gb"],
            "disk_used_gb": disk["used_gb"],
            "disk_total_gb": disk["total_gb"],
            "disk_usage_percent": disk["usage_percent"],
            "internet_available": stats["network"]["internet_available"],
            "top_memory_processes": [
                {"name": p.get("name"), "pid": p.get("pid"),
                 "ram_mb": p.get("memory_mb"), "ram_pct": p.get("memory_percent")}
                for p in process_engine.get_top_memory_processes(limit=5)
            ],
            "top_cpu_processes": [
                {"name": p.get("name"), "pid": p.get("pid"),
                 "cpu_pct": p.get("cpu_percent"), "ram_mb": p.get("memory_mb")}
                for p in process_engine.get_top_cpu_processes(limit=5)
            ],
        }

    # ──────────────────────────────────────────────────────────────────
    # Main entry point: local rules first, selected AI provider if needed
    # ──────────────────────────────────────────────────────────────────
    def plan_and_execute(
        self,
        query: str,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle recognized requests locally; ask the selected provider only for
        requests that the local rules do not recognize.
        """
        target_path = parse_file_creation_request(query)
        if target_path is not None:
            if not target_path:
                return {
                    "intent": "FILE_CREATE",
                    "response": "Please specify the full path and file name, for example `create file C:\\Users\\you\\Desktop\\notes.txt`.",
                    "tools_used": [],
                    "execution_steps": [],
                    "root_cause": None,
                    "commands": [],
                    "recommendations": ["Provide an absolute path and file name."],
                }
            return self._handle_file_create(target_path, query)

        try:
            directory_request = parse_directory_listing_request(query)
        except ValueError as exc:
            return self._directory_listing_error(query, str(exc))
        if directory_request is not None:
            directory, limit = directory_request
            return self._handle_directory_listing(directory, limit, query)

        telemetry_ctx: Dict[str, Any] = {}
        ai_result = self._local_rule_planner(query, telemetry_ctx)
        if ai_result and ai_result.get("intent") == "GREETING":
            telemetry_ctx = self._build_telemetry_context()

        if not ai_result:
            if self._needs_telemetry(query):
                telemetry_ctx = self._build_telemetry_context()
            ai_result = llm_gateway.reason_and_plan(query, telemetry_ctx, provider, api_key, model)

        if not ai_result:
            # Hard fallback: no cloud or local model provider is available.
            return self._offline_fallback(query, telemetry_ctx, provider)

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

    def _handle_directory_listing(self, requested_path: str, limit: int, query: str) -> Dict[str, Any]:
        try:
            directory, files = list_directory_files(requested_path, limit)
        except (ValueError, PermissionError, OSError) as exc:
            return self._directory_listing_error(query, str(exc))

        if files:
            file_rows = "\n".join(f"- `{file_path.name}`" for file_path in files)
            response = (
                f"### Local Directory Listing\n\n"
                f"Folder: `{directory}`\n\n{file_rows}"
            )
        else:
            response = f"### Local Directory Listing\n\nNo files found in `{directory}`."

        root_nodes = [
            {"id": "request", "label": "List folder files", "type": "process"},
            {"id": "directory", "label": str(directory), "type": "system"},
            {"id": "results", "label": f"{len(files)} file(s)", "type": "impact"},
        ]
        root_edges = [
            {"from": "request", "to": "directory"},
            {"from": "directory", "to": "results"},
        ]
        self._save_history(
            query,
            response,
            ["local_directory_listing"],
            root_nodes,
            root_edges,
            [],
            intent="DIRECTORY_LISTING",
        )
        return {
            "intent": "DIRECTORY_LISTING",
            "response": response,
            "tools_used": ["local_directory_listing"],
            "execution_steps": [{
                "tool": "local_directory_listing",
                "label": f"Listed {len(files)} file(s) in {directory}",
                "status": "done",
            }],
            "root_cause": {"nodes": root_nodes, "edges": root_edges},
            "commands": [],
            "recommendations": [],
        }

    def _directory_listing_error(self, query: str, reason: str) -> Dict[str, Any]:
        response = f"### Could Not List Folder\n\n{reason}"
        self._save_history(
            query,
            response,
            ["local_directory_listing"],
            [{"id": "error", "label": "Directory listing failed", "type": "system"}],
            [],
            [],
            intent="DIRECTORY_LISTING",
        )
        return {
            "intent": "DIRECTORY_LISTING",
            "response": response,
            "tools_used": ["local_directory_listing"],
            "execution_steps": [{
                "tool": "local_directory_listing",
                "label": "Directory listing failed",
                "status": "error",
            }],
            "root_cause": {
                "nodes": [{"id": "error", "label": "Directory listing failed", "type": "system"}],
                "edges": [],
            },
            "commands": [],
            "recommendations": ["Check the folder path and Windows permissions."],
        }

    @staticmethod
    def _needs_telemetry(query: str) -> bool:
        terms = (
            "cpu", "processor", "memory", "ram", "disk", "storage",
            "performance", "slow", "health", "temperature", "process",
        )
        query_lower = query.lower()
        return any(term in query_lower for term in terms)

    def _handle_file_create(self, requested_path: str, query: str) -> Dict[str, Any]:
        try:
            target_path = validate_file_target(requested_path)
        except ValueError as exc:
            return {
                "intent": "FILE_CREATE",
                "response": f"### File was not created\n\n{exc}",
                "tools_used": [],
                "execution_steps": [],
                "root_cause": None,
                "commands": [],
                "recommendations": ["Correct the path and try again."],
            }

        command = {
            "id": f"cmd-{uuid.uuid4().hex[:8]}",
            "command": f"Create empty file: {target_path}",
            "action": "create_file",
            "file_path": str(target_path),
            "risk_level": "LOW",
            "explanation": (
                "Creates a new, empty file only after you click Execute. "
                "An existing file will not be overwritten."
            ),
        }
        response_md = (
            "### Create Empty File\n\n"
            f"Target: `{target_path}`\n\n"
            "Review the path and click **Execute** to create the file. "
            "If a file already exists there, it will be left unchanged."
        )
        root_nodes = [
            {"id": "request", "label": "Create file", "type": "process"},
            {"id": "target", "label": str(target_path), "type": "system"},
            {"id": "approval", "label": "Waiting for your approval", "type": "impact"},
        ]
        root_edges = [
            {"from": "request", "to": "target"},
            {"from": "target", "to": "approval"},
        ]
        commands = [command]
        self._save_history(
            query,
            response_md,
            ["local_file_creator"],
            root_nodes,
            root_edges,
            commands,
            intent="FILE_CREATE",
        )
        return {
            "intent": "FILE_CREATE",
            "response": response_md,
            "tools_used": ["local_file_creator"],
            "execution_steps": [
                {"tool": "local_file_creator", "label": "Prepared a safe file creation action", "status": "done"}
            ],
            "root_cause": {"nodes": root_nodes, "edges": root_edges},
            "commands": commands,
            "recommendations": ["Verify the target path before approving."],
        }

    # ──────────────────────────────────────────────────────────────────
    # Handler: Greeting
    # ──────────────────────────────────────────────────────────────────
    def _format_greeting(self, ai_result: Dict, telemetry: Dict, provider: str) -> Dict:
        response_md = ai_result.get("response_markdown", "")
        if not response_md:
            cpu = format_metric(telemetry.get("cpu_usage_percent"), suffix="%")
            ram = format_metric(telemetry.get("memory_percent"), suffix="%")
            health_value = telemetry.get("system_health_score")
            health = (
                f"{health_value}/100"
                if isinstance(health_value, (int, float))
                else "Unavailable"
            )
            host = telemetry.get("host", {}).get("os_name", "Unavailable")
            response_md = f"""### 👋 Hello! I am KernelSense AI

I am your system assistant, powered by **{provider}**. Detected host: **{host}**.

---

#### 🛠️ What I Can Do:
1. **Host information:** Ask about the detected operating system and live metrics.
2. **Hardware telemetry:** Health: `{health}` | RAM: `{ram}` | CPU: `{cpu}`
3. **Local file search:** Ask me to find a file by its name.
4. **Web and apps:** Ask to open a website or an installed application.
5. **AI chat:** Ask for explanations or system diagnostics.

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
                "Ask about the detected host or current system metrics."
            ])
        }

    # ──────────────────────────────────────────────────────────────────
    # Handler: File Search — Gemini identifies the file, we search drive
    # ──────────────────────────────────────────────────────────────────
    def _handle_file_search(self, ai_result: Dict, query: str) -> Dict:
        search_target = ai_result.get("search_target") or query
        files = file_finder.search_files(search_target, max_results=6)
        if not files and search_target != query:
            files = file_finder.search_files(query, max_results=6)

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
        explanation  = ai_result.get("linux_explanation") or f"Executes `{raw_command}` inside the Ubuntu Linux environment."
        task_type    = ai_result.get("linux_task_type") or "RAW_COMMAND"
        provider     = ai_result.get("provider", "gemini")

        # For IP address queries: show BOTH Windows host IP (matching ipconfig) AND Ubuntu WSL2 IP
        if task_type == "IP_ADDRESS" or ("ip" in query.lower() and ("address" in query.lower() or "my ip" in query.lower() or "config" in query.lower())):
            raw_command = (
                "echo '=== [1/3] Windows Host IP (Wi-Fi / LAN) ==='; "
                "ipconfig.exe | grep -i 'IPv4' | tr -d '\\r'; echo ''; "
                "echo '=== [2/3] Ubuntu Linux (WSL2) Virtual IP ==='; "
                "hostname -I 2>/dev/null || ip -br a; echo ''; "
                "echo '=== [3/3] Public Internet IP ==='; "
                "curl -s --max-time 2 ifconfig.me 2>/dev/null && echo '' || echo 'N/A'"
            )
            title = "🌐 Comprehensive Windows Host & Ubuntu WSL2 IP Discovery"
            explanation = "Queries Windows ipconfig.exe for your physical Wi-Fi/LAN IP, Ubuntu Linux for the WSL2 virtual IP, and checks your public internet IP."

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
        safe_shell_action = shell_action.replace('"', r'\"')

        ubuntu_cmd = (
            f'wsl.exe -d Ubuntu bash -c "'
            f'echo =================================================; '
            f'echo  KernelSense: Launching {display_title}; '
            f'echo =================================================; '
            f'{safe_shell_action}; '
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

        # Keep the agent's Windows command intact; show its risk before approval.
        proposed_commands = []
        blocked_reason = None
        raw_commands = ai_result.get("proposed_commands", [])
        if not isinstance(raw_commands, list) or ai_result.get("intent") == "NEEDS_CLARIFICATION":
            raw_commands = []
        for pc in raw_commands[:1]:
            if not isinstance(pc, dict):
                continue
            raw = pc.get("command", "")
            if isinstance(raw, str) and raw.strip():
                local_risk = command_safety_engine.evaluate_risk(raw)
                if not local_risk["safe"]:
                    blocked_reason = local_risk["explanation"]
                    continue
                ai_risk = str(pc.get("risk_level", "HIGH")).upper()
                risk_levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
                if ai_risk not in risk_levels:
                    ai_risk = "HIGH"
                effective_risk = max(
                    (ai_risk, local_risk["risk_level"]),
                    key=lambda level: risk_levels.get(level, 2),
                )
                risk_reason = str(pc.get("risk_reason", "")).strip()
                if not risk_reason:
                    risk_reason = "AI risk assessment was missing; treated as high risk."
                if local_risk["risk_level"] != "LOW":
                    risk_reason = "; ".join(
                        part for part in (risk_reason, local_risk["explanation"]) if part
                    )
                proposed_commands.append({
                    "id": f"cmd-{uuid.uuid4().hex[:8]}",
                    "command": raw,
                    "risk_level": effective_risk,
                    "risk_reason": risk_reason,
                    "explanation": pc.get("explanation", ""),
                })

        if proposed_commands:
            response_md = (
                "### Command ready for approval\n\n"
                "The command has not run yet. Review its risk and click **Execute** "
                "to run it; captured output will appear below the command."
            )
        elif blocked_reason:
            response_md = f"### Command blocked\n\n{blocked_reason}"

        health = telemetry.get("system_health_score")
        health_label = f"{health}%" if isinstance(health, (int, float)) else "unavailable"
        root_nodes = ai_result.get("root_cause_nodes") or [
            {"id": "q",  "label": f"Query: {query[:30]}", "type": "process"},
            {"id": "ai", "label": f"AI Agent ({provider})", "type": "system"},
            {"id": "hw", "label": f"Health: {health_label}", "type": "impact"}
        ]
        root_edges = ai_result.get("root_cause_edges") or [
            {"from": "q", "to": "ai"}, {"from": "ai", "to": "hw"}
        ]

        intent_name = ai_result.get("intent", "GENERAL_QUERY")
        self._save_history(query, response_md, ["ai_agent"], root_nodes, root_edges, proposed_commands, intent=intent_name)
        return {
            "response": response_md,
            "tools_used": ["ai_agent"] + (["telemetry_collector"] if telemetry else []),
            "execution_steps": (
                [{"tool": "telemetry_collector", "label": "Sampled live OS telemetry", "status": "done"}]
                if telemetry else []
            ) + [{"tool": "ai_agent", "label": f"Reasoned with {provider}", "status": "done"}],
            "root_cause": {"nodes": root_nodes, "edges": root_edges},
            "commands": proposed_commands,
            "recommendations": ai_result.get("recommendations", [])
        }

    # ──────────────────────────────────────────────────────────────────
    # Local rules handle common requests before any provider call.
    # ──────────────────────────────────────────────────────────────────
    def _local_rule_planner(self, query: str, telemetry: Dict) -> Optional[Dict[str, Any]]:
        q = query.strip().lower()

        # 1. Greeting
        if q in {"hi", "hello", "hey", "who are you", "what can you do", "help"}:
            return {
                "intent": "GREETING",
                "action_type": "CHAT",
                "provider": "local_offline_engine",
                "response_markdown": ""
            }

        # 2. File search / open
        has_ext = bool(re.search(r'\.(pdf|docx?|pptx?|xlsx?|txt|csv|png|jpe?g|json|log|py|java|cpp|c|html|css|js)\b', q, re.I))
        file_search_prefixes = (
            "find ", "search ", "search for ", "locate ", "open ", "read ", "show "
        )
        is_file_search = any(q.startswith(prefix) for prefix in file_search_prefixes) and has_ext
        is_file_search = is_file_search or any(
            phrase in q for phrase in ("find file ", "search files ", "locate file ")
        )
        if is_file_search and not q.startswith(("open chrome", "open brave")):
            target = file_finder.clean_target(query)
            return {
                "intent": "FILE_SEARCH",
                "action_type": "FILE_OPEN",
                "search_target": target,
                "provider": "local_offline_engine"
            }

        # 3. Open URL in Browser
        if any(site in q for site in ["youtube", "google", "github", "reddit", "netflix", "stackoverflow", "twitter", "x.com", "instagram", "facebook", "wikipedia"]) or "http" in q or ".com" in q:
            browser = "chrome"
            for b in ["brave", "edge", "firefox", "chrome"]:
                if b in q:
                    browser = b
                    break
            url = None
            if "youtube" in q:
                url = "https://www.youtube.com"
            elif "google" in q:
                url = "https://www.google.com"
            elif "github" in q:
                url = "https://github.com"
            elif "reddit" in q:
                url = "https://reddit.com"
            elif "netflix" in q:
                url = "https://www.netflix.com"
            else:
                url = f"https://{q.split()[-1]}"
            return {
                "intent": "OPEN_URL_IN_APP",
                "action_type": "OPEN_URL",
                "target_url": url,
                "browser": browser,
                "provider": "local_offline_engine"
            }

        # 4. Open Desktop Application
        if any(q.startswith(p) for p in ["open ", "launch ", "start ", "run "]):
            app_raw = re.sub(r'^(open|launch|start|run)\s+', '', q).strip()
            from windows.apps import app_registry
            found_app = app_registry.find_app(app_raw)
            if found_app or app_raw in {"notepad", "calculator", "calc", "cmd", "terminal", "taskmgr", "paint", "explorer"}:
                return {
                    "intent": "OPEN_APPLICATION",
                    "action_type": "OPEN_APP",
                    "target_app": app_raw,
                    "provider": "local_offline_engine"
                }

        # 5. Linux Core Command (IP address, whoami, ports, cpu info, disk)
        if any(k in q for k in ["ip address", "my ip", "ipconfig", "what is my ip"]):
            return {
                "intent": "LINUX_CORE_COMMAND",
                "action_type": "LINUX_SHELL",
                "linux_task_type": "IP_ADDRESS",
                "linux_command": "hostname -I; ip -br a",
                "linux_title": "🌐 Comprehensive Windows Host & Ubuntu WSL2 IP Discovery",
                "provider": "local_offline_engine"
            }
        if any(k in q for k in ["whoami", "my username", "current user"]):
            return {
                "intent": "LINUX_CORE_COMMAND",
                "action_type": "LINUX_SHELL",
                "linux_task_type": "USER_IDENTITY",
                "linux_command": "whoami; id; w",
                "linux_title": "👤 Linux User Identity & Active Sessions",
                "provider": "local_offline_engine"
            }
        if any(k in q for k in ["open ports", "listening ports", "active ports"]):
            return {
                "intent": "LINUX_CORE_COMMAND",
                "action_type": "LINUX_SHELL",
                "linux_task_type": "OPEN_PORTS",
                "linux_command": "ss -tulnp",
                "linux_title": "🔌 Active Listening Network Ports",
                "provider": "local_offline_engine"
            }
        if any(k in q for k in ["lscpu", "cpu info", "processor info"]):
            return {
                "intent": "LINUX_CORE_COMMAND",
                "action_type": "LINUX_SHELL",
                "linux_task_type": "CPU_INFO",
                "linux_command": "lscpu",
                "linux_title": "⚡ CPU Architecture & Core Details",
                "provider": "local_offline_engine"
            }
        if any(k in q for k in ["current directory", "pwd", "working directory"]):
            return {
                "intent": "LINUX_CORE_COMMAND",
                "action_type": "LINUX_SHELL",
                "linux_task_type": "DIR_LIST",
                "linux_command": "pwd; ls -la",
                "linux_title": "📂 Working Directory & Files",
                "provider": "local_offline_engine"
            }

        return None

    # ──────────────────────────────────────────────────────────────────
    # Hard offline fallback (all providers unreachable)
    # ──────────────────────────────────────────────────────────────────
    def _offline_fallback(self, query: str, telemetry: Dict, provider: str = "gemini") -> Dict:
        mem = telemetry.get("memory_percent")
        cpu = telemetry.get("cpu_usage_percent")
        health = telemetry.get("system_health_score")
        top_mem = telemetry.get("top_memory_processes", [])
        top_cpu = telemetry.get("top_cpu_processes", [])

        mem_rows = "\n".join(
            f"| `{p.get('name') or 'Not reported'}` | `{p.get('pid') or 'Not reported'}` | "
            f"`{format_metric(p.get('ram_mb'), suffix=' MB')}` | "
            f"`{format_metric(p.get('ram_pct'), suffix='%')}` |"
            for p in top_mem[:4]
        ) or "| No process data available | - | - | - |"
        cpu_rows = "\n".join(
            f"| `{p.get('name') or 'Not reported'}` | `{p.get('pid') or 'Not reported'}` | "
            f"`{format_metric(p.get('cpu_pct'), suffix='%')}` |"
            for p in top_cpu[:4]
        ) or "| No process data available | - | - |"

        host = telemetry.get("host", {})
        health_text = f"{health}/100" if isinstance(health, (int, float)) else "Unavailable"
        network = telemetry.get("internet_available")
        network_text = "Online" if network is True else "Offline" if network is False else "Unavailable"
        api_key_name = "GROK_API_KEY" if provider == "grok" else "GEMINI_API_KEY"
        response_md = f"""### 🛡️ KernelSense System Status (Offline Mode)

> **⚠️ Selected AI Provider Unavailable** — {provider} did not answer; no provider switch was made. Values below come from the host telemetry collector.

#### 📊 Live Hardware Telemetry:
* **Operating System:** `{host.get('os_name') or 'Unavailable'}`
* **System Health:** `{health_text}`
* **CPU Usage:** `{format_metric(cpu, suffix='%')}`
* **RAM Usage:** `{format_metric(mem, suffix='%')}` (`{format_metric(telemetry.get('memory_used_gb'), suffix=' GB')}` / `{format_metric(telemetry.get('memory_total_gb'), suffix=' GB')}`)
* **Disk Usage:** `{format_metric(telemetry.get('disk_usage_percent'), suffix='%')}`
* **Network Connectivity:** `{network_text}`

#### 🏆 Top RAM Consumers:
| Process | PID | RAM | % |
| :--- | :--- | :--- | :--- |
{mem_rows}

#### ⚡ Top CPU Consumers:
| Process | PID | CPU % |
| :--- | :--- | :--- |
{cpu_rows}

*Check your network connection and verify the `{api_key_name}` key.*
"""
        return {
            "response": response_md,
            "tools_used": ["telemetry_collector"],
            "execution_steps": [{"tool": "telemetry_collector", "label": "Offline mode — live telemetry only", "status": "done"}],
            "root_cause": {
                "nodes": [{"id": "offline", "label": "AI Provider Offline", "type": "system"}],
                "edges": []
            },
            "commands": [],
            "recommendations": [
                f"Check {api_key_name} is set correctly in backend/.env",
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
