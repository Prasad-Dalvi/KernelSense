"""
Command Safety & Multi-Layer Execution Sandbox for KernelSense
Enforces security blast radius analysis and visible interactive terminal dispatching.
"""

import re
import os
import platform
import subprocess
from typing import Dict, Any, Tuple

class CommandSafetyEngine:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        
        # Heuristic rules for dangerous operations
        self.dangerous_patterns = [
            (r'rm\s+-rf\s+/', "Root filesystem deletion is strictly blocked."),
            (r'rm\s+-rf\s+/\*', "Wildcard root deletion is strictly blocked."),
            (r'mkfs', "Filesystem formatting is strictly blocked."),
            (r'dd\s+if=.*of=/dev/[sh]d[a-z]', "Raw disk overwrite is strictly blocked."),
            (r'>\s+/dev/[sh]d[a-z]', "Raw disk redirection is strictly blocked."),
            (r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', "Fork bomb is strictly blocked."),
            (r'chmod\s+-R\s+777\s+/', "Root permission wipe is strictly blocked."),
            (r'format\s+[a-zA-Z]:', "Windows disk formatting is strictly blocked."),
            (r'diskpart', "Diskpart raw partitioning is blocked.")
        ]
        
        self.high_risk_patterns = [
            r'kill\s+-9',
            r'taskkill\s+/f',
            r'systemctl\s+stop',
            r'service\s+.*stop',
            r'drop_caches',
            r'shutdown',
            r'reboot'
        ]

    def evaluate_risk(self, command: str) -> Dict[str, Any]:
        """Classifies a shell command into LOW, MEDIUM, or HIGH risk with security explanations."""
        cmd_clean = command.strip()
        
        # Check hard blocks
        for pattern, reason in self.dangerous_patterns:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return {
                    "risk_level": "CRITICAL_BLOCKED",
                    "safe": False,
                    "explanation": reason,
                    "requires_approval": False
                }
                
        # Check high risk
        for pattern in self.high_risk_patterns:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return {
                    "risk_level": "HIGH",
                    "safe": True,
                    "explanation": "Modifies running system services or forcibly terminates processes.",
                    "requires_approval": True
                }
                
        # Check medium risk (network binds, package managers, writes)
        if any(w in cmd_clean.lower() for w in ['apt', 'pip', 'npm', 'curl', 'wget', 'chown', 'chmod', 'sed', 'awk', 'reg', 'netsh']):
            return {
                "risk_level": "MEDIUM",
                "safe": True,
                "explanation": "Executes package modifications or alters local configurations.",
                "requires_approval": True
            }
            
        # Default read-only / diagnostic inspection
        return {
            "risk_level": "LOW",
            "safe": True,
            "explanation": "Standard diagnostic inspection or safe application launch.",
            "requires_approval": True
        }

    def execute_command(self, command: str, timeout_sec: int = 10) -> Dict[str, Any]:
        """
        Executes approved commands:
        1. If WSL / Ubuntu terminal command: Spawns visible interactive window on desktop (cmd.exe /c start wsl.exe ...)
        2. If Browser / URL launch: Spawns visible browser window on desktop
        3. If GUI application: Spawns visible interactive window on desktop
        4. If standard shell: Executes safely and captures output
        """
        safety = self.evaluate_risk(command)
        if safety["risk_level"] == "CRITICAL_BLOCKED":
            return {
                "success": False,
                "output": f"SECURITY SHIELD BLOCKED: {safety['explanation']}",
                "status": "blocked"
            }

        exec_cmd = command.strip()

        # ─── A. WSL / Interactive Ubuntu Terminal Commands ────────────────────
        if 'wsl' in exec_cmd.lower() or 'ubuntu' in exec_cmd.lower():
            try:
                # Fix bare Windows desktop app invocations inside WSL command if needed
                fixed_cmd = exec_cmd
                app_map = {
                    'calculator': 'calc',
                    'calc': 'calc',
                    'notepad': 'notepad',
                    'mspaint': 'mspaint',
                    'paint': 'mspaint',
                    'whatsapp': 'whatsapp:',
                    'watsapp': 'whatsapp:',
                    'whatsup': 'whatsapp:',
                    'spotify': 'spotify',
                    'taskmgr': 'taskmgr',
                    'task manager': 'taskmgr',
                    'explorer': 'explorer'
                }
                detected_win_app = None
                for k in sorted(app_map.keys(), key=len, reverse=True):
                    pattern = rf'(?<!start\s)(?<!start\s"")\b{re.escape(k)}\b(?=\s*;|\s*&&|\s*\"|\s*\')'
                    if re.search(pattern, fixed_cmd, re.I):
                        detected_win_app = app_map[k]
                        fixed_cmd = re.sub(pattern, f'cmd.exe /c start {detected_win_app}', fixed_cmd, count=1, flags=re.I)
                        break

                # Wrap with cmd.exe /c start to guarantee visible interactive console on desktop
                if not fixed_cmd.startswith('cmd.exe /c start'):
                    spawn_cmd = f'cmd.exe /c start {fixed_cmd}'
                else:
                    spawn_cmd = fixed_cmd
                    
                subprocess.Popen(spawn_cmd, shell=True)

                # Direct parallel Windows launch for instant responsiveness
                if detected_win_app:
                    try:
                        if detected_win_app.endswith(':'):
                            subprocess.Popen(f'powershell.exe -NoProfile -Command "Start-Process \'{detected_win_app}\'"', shell=True)
                        else:
                            subprocess.Popen(f'cmd.exe /c start {detected_win_app}', shell=True)
                    except Exception:
                        pass

                return {
                    "success": True,
                    "output": f"Successfully spawned interactive Ubuntu terminal window executing:\n$ {fixed_cmd}",
                    "status": "success"
                }
            except Exception as e:
                return {"success": False, "output": f"Failed to spawn Ubuntu window: {str(e)}", "status": "error"}

        # ─── B. Browser URL Launching ─────────────────────────────────────────
        if ('start ' in exec_cmd.lower() or 'cmd.exe /c start' in exec_cmd.lower()) and ('http://' in exec_cmd.lower() or 'https://' in exec_cmd.lower()):
            try:
                if not exec_cmd.startswith('cmd.exe /c start'):
                    spawn_cmd = f'cmd.exe /c start {exec_cmd.replace("start ", "")}'
                else:
                    spawn_cmd = exec_cmd
                subprocess.Popen(spawn_cmd, shell=True)
                return {
                    "success": True,
                    "output": f"Successfully opened website in browser:\n$ {exec_cmd}",
                    "status": "success"
                }
            except Exception as e:
                return {"success": False, "output": f"Failed to open browser: {str(e)}", "status": "error"}

        # ─── C. GUI Application Launches ──────────────────────────────────────
        is_start_cmd = exec_cmd.lower().startswith('start ') or 'start-process' in exec_cmd.lower()
        gui_apps = ['notepad', 'calc', 'setting', 'paint', 'mspaint', 'brave', 'chrome', 'edge', 'explorer', 'taskmgr', 'spotify', 'code', 'vscode']
        is_gui_target = any(app in exec_cmd.lower() for app in gui_apps) and not any(k in exec_cmd.lower() for k in ['taskkill', 'kill', 'get-process'])

        if is_start_cmd or is_gui_target:
            try:
                from windows.apps import launch_application
                app_target = exec_cmd.replace('start ', '').replace('Start-Process ', '').replace('.exe', '').strip().strip('"').strip("'")
                res = launch_application(app_target)
                return {
                    "success": res.get("success", True),
                    "output": res.get("output", f"Successfully launched '{app_target}' on your desktop."),
                    "status": "success" if res.get("success", True) else "error"
                }
            except Exception as e:
                return {"success": False, "output": f"Failed to launch GUI application: {str(e)}", "status": "error"}

        # ─── D. Standard Shell / Non-blocking Execution ───────────────────────
        try:
            res = subprocess.run(
                exec_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            output = res.stdout if res.returncode == 0 else (res.stderr or f"Exited with code {res.returncode}")
            return {
                "success": res.returncode == 0,
                "output": output.strip() or "Command completed with no output.",
                "status": "success" if res.returncode == 0 else "error"
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": f"Command timed out after {timeout_sec} seconds.", "status": "timeout"}
        except Exception as e:
            return {"success": False, "output": str(e), "status": "error"}

command_safety_engine = CommandSafetyEngine()
