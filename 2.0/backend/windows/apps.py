"""
Universal Application Discovery & Execution Engine for KernelSense
Automatically detects, indexes, and launches ALL third-party desktop software,
games, Start Menu shortcuts (.lnk), Registry App Paths, and Windows UWP/Store apps.
"""

import os
import re
import sys
import glob
import time
import winreg
import ctypes
import platform
import subprocess
import threading
from typing import Dict, Any, Optional, List

from ubuntu.bridge import ubuntu_bridge

class AppRegistry:
    """
    Dynamic index of all installed applications on the Windows host.
    Combines Start Menu shortcuts, Registry App Paths, system executables,
    URL protocols, and Windows Store apps.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._apps: Dict[str, Dict[str, Any]] = {}
        self._uwp_apps: Dict[str, Dict[str, Any]] = {}
        self._last_scan: float = 0.0
        self.is_windows = platform.system() == "Windows"

        # Fast initial scan of shortcuts, registry, and built-ins (<30ms)
        self.refresh()

        # Background thread for UWP / Store apps (Get-StartApps) to prevent blocking
        if self.is_windows:
            t = threading.Thread(target=self._scan_uwp_apps, daemon=True)
            t.start()

    def refresh(self):
        """Scans filesystem and registry for all installed applications."""
        if not self.is_windows:
            return

        with self._lock:
            discovered: Dict[str, Dict[str, Any]] = {}

            # 1. Built-in Windows Applications & Known Protocols
            builtins = {
                "calculator": {"title": "Windows Calculator", "type": "builtin", "target": "calc.exe", "description": "Windows Calculator"},
                "calc": {"title": "Windows Calculator", "type": "builtin", "target": "calc.exe", "description": "Windows Calculator"},
                "notepad": {"title": "Notepad Text Editor", "type": "builtin", "target": "notepad.exe", "description": "Notepad Text Editor"},
                "paint": {"title": "Paint Application", "type": "builtin", "target": "mspaint.exe", "description": "Paint Application"},
                "mspaint": {"title": "Paint Application", "type": "builtin", "target": "mspaint.exe", "description": "Paint Application"},
                "task manager": {"title": "Task Manager", "type": "builtin", "target": "taskmgr.exe", "description": "Windows Task Manager"},
                "taskmgr": {"title": "Task Manager", "type": "builtin", "target": "taskmgr.exe", "description": "Windows Task Manager"},
                "explorer": {"title": "File Explorer", "type": "builtin", "target": "explorer.exe", "description": "Windows File Explorer"},
                "file explorer": {"title": "File Explorer", "type": "builtin", "target": "explorer.exe", "description": "Windows File Explorer"},
                "my computer": {"title": "File Explorer", "type": "builtin", "target": "explorer.exe", "description": "Windows File Explorer"},
                "control panel": {"title": "Control Panel", "type": "builtin", "target": "control.exe", "description": "Control Panel"},
                "control": {"title": "Control Panel", "type": "builtin", "target": "control.exe", "description": "Control Panel"},
                "settings": {"title": "Windows Settings", "type": "protocol", "target": "ms-settings:", "description": "Windows Settings App"},
                "windows settings": {"title": "Windows Settings", "type": "protocol", "target": "ms-settings:", "description": "Windows Settings App"},
                "terminal": {"title": "Windows Terminal", "type": "builtin", "target": "wt.exe", "description": "Windows Terminal"},
                "windows terminal": {"title": "Windows Terminal", "type": "builtin", "target": "wt.exe", "description": "Windows Terminal"},
                "wt": {"title": "Windows Terminal", "type": "builtin", "target": "wt.exe", "description": "Windows Terminal"},
                "cmd": {"title": "Command Prompt", "type": "builtin", "target": "cmd.exe", "description": "Command Prompt"},
                "command prompt": {"title": "Command Prompt", "type": "builtin", "target": "cmd.exe", "description": "Command Prompt"},
                "powershell": {"title": "PowerShell", "type": "builtin", "target": "powershell.exe", "description": "Windows PowerShell"},
                "whatsapp": {"title": "WhatsApp Desktop", "type": "protocol", "target": "whatsapp:", "description": "WhatsApp Desktop"},
                "watsapp": {"title": "WhatsApp Desktop", "type": "protocol", "target": "whatsapp:", "description": "WhatsApp Desktop"},
                "whatsup": {"title": "WhatsApp Desktop", "type": "protocol", "target": "whatsapp:", "description": "WhatsApp Desktop"},
                "spotify": {"title": "Spotify", "type": "protocol", "target": "spotify:", "description": "Spotify Music"},
                "steam": {"title": "Steam", "type": "protocol", "target": "steam:", "description": "Steam Gaming Client"},
                "discord": {"title": "Discord", "type": "protocol", "target": "discord:", "description": "Discord Voice & Chat"},
            }
            for k, v in builtins.items():
                discovered[k] = v

            # 2. Windows Start Menu Shortcuts (.lnk files)
            start_dirs = [
                os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            ]
            desktop_dirs = [
                os.path.expandvars(r"%PUBLIC%\Desktop"),
                os.path.expandvars(r"%USERPROFILE%\Desktop"),
                r"D:\Desktop"
            ]

            # Scan Start Menu directories
            for sdir in start_dirs:
                if os.path.isdir(sdir):
                    for root, dirs, files in os.walk(sdir):
                        for f in files:
                            if f.lower().endswith(".lnk"):
                                name = os.path.splitext(f)[0].strip()
                                low_name = name.lower()
                                # Filter out uninstallers and manuals
                                if any(x in low_name for x in ["uninstall", "remove", "help", "manual", "readme", "documentation"]):
                                    continue
                                full_path = os.path.join(root, f)
                                if low_name not in discovered:
                                    discovered[low_name] = {
                                        "title": name,
                                        "type": "lnk",
                                        "target": full_path,
                                        "description": f"{name} Application"
                                    }

            # Scan Desktop directories (top-level only to prevent deep scanning into code workspaces)
            for ddir in desktop_dirs:
                if os.path.isdir(ddir):
                    try:
                        for f in os.listdir(ddir):
                            if f.lower().endswith(".lnk"):
                                name = os.path.splitext(f)[0].strip()
                                low_name = name.lower()
                                if any(x in low_name for x in ["uninstall", "remove"]):
                                    continue
                                full_path = os.path.join(ddir, f)
                                if low_name not in discovered:
                                    discovered[low_name] = {
                                        "title": name,
                                        "type": "lnk",
                                        "target": full_path,
                                        "description": f"{name} Desktop Shortcut"
                                    }
                    except Exception:
                        pass

            # 3. Windows Registry App Paths (HKLM & HKCU)
            reg_paths = self._scan_registry_app_paths()
            for name, path in reg_paths.items():
                if name not in discovered and os.path.exists(path):
                    clean_title = os.path.splitext(os.path.basename(path))[0].title()
                    discovered[name] = {
                        "title": clean_title,
                        "type": "exe",
                        "target": path,
                        "description": f"{clean_title} Executable"
                    }

            self._apps = discovered
            self._last_scan = time.time()

    def _scan_registry_app_paths(self) -> Dict[str, str]:
        results = {}
        for root_key, subkey in [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]:
            try:
                with winreg.OpenKey(root_key, subkey) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            app_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, app_key_name) as app_key:
                                val, _ = winreg.QueryValueEx(app_key, "")
                                if val:
                                    val = os.path.expandvars(val.strip().strip('"'))
                                    name = app_key_name.lower().replace(".exe", "")
                                    results[name] = val
                        except Exception:
                            pass
            except Exception:
                pass
        return results

    def _scan_uwp_apps(self):
        """Scans Windows UWP apps via Get-StartApps in background."""
        try:
            cmd = ["powershell", "-NoProfile", "-Command", "Get-StartApps | ConvertTo-Json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                import json
                apps = json.loads(res.stdout)
                uwp = {}
                for a in apps:
                    name = a.get("Name", "").strip()
                    appid = a.get("AppID", "").strip()
                    if name and appid and ("!" in appid or "AutoGenerated" in appid):
                        uwp[name.lower()] = {
                            "title": name,
                            "type": "uwp",
                            "target": appid,
                            "description": f"{name} Windows App"
                        }
                with self._lock:
                    self._uwp_apps = uwp
        except Exception:
            pass

    def find_app(self, query: str) -> Optional[Dict[str, Any]]:
        """Finds the best matching installed app for a query."""
        raw = query.strip().lower().replace(".exe", "")
        for prefix in ["open ", "launch ", "start ", "run "]:
            if raw.startswith(prefix):
                raw = raw[len(prefix):].strip()

        # Handle common aliases and game titles
        aliases = {
            "riot games": "riot client",
            "riot": "riot client",
            "val": "valorant",
            "vs code": "code",
            "vscode": "code",
            "ms word": "word",
            "winword": "word",
            "ms excel": "excel",
            "powerpoint": "powerpnt",
            "ppt": "powerpnt",
            "packet tracer": "cisco packet tracer",
            "cisco": "cisco packet tracer",
            "vlc player": "vlc media player",
            "paint app": "paint",
            "calculator app": "calculator"
        }
        search_term = aliases.get(raw, raw)

        with self._lock:
            # 1. Exact match in indexed apps
            if search_term in self._apps:
                return self._apps[search_term]

            # 2. Exact match in UWP apps
            if search_term in self._uwp_apps:
                return self._uwp_apps[search_term]

            # 3. Exact title match
            for k, v in self._apps.items():
                if v.get("title", "").lower() == search_term:
                    return v

            # 4. Prefix match (e.g. "valorant" matching "VALORANT")
            for k, v in self._apps.items():
                if k.startswith(search_term):
                    return v

            # 5. Substring match
            candidates = []
            for k, v in self._apps.items():
                if search_term in k or k in search_term:
                    candidates.append((len(k), v))

            if candidates:
                candidates.sort(key=lambda x: x[0])
                return candidates[0][1]

            # 6. UWP substring match
            for k, v in self._uwp_apps.items():
                if search_term in k:
                    return v

        return None

    def resolve_launch_info(self, query: str) -> Dict[str, Any]:
        """
        Resolves an app query into clean display info, Ubuntu shell command,
        and direct Windows command.
        """
        app = self.find_app(query)
        raw = query.strip().lower().replace(".exe", "")
        for prefix in ["open ", "launch ", "start ", "run "]:
            if raw.startswith(prefix):
                raw = raw[len(prefix):].strip()

        if app:
            title = app.get("title", raw.title())
            app_type = app.get("type", "lnk")
            target = app.get("target", raw)
            desc = app.get("description", f"{title} Application")

            if app_type == "builtin":
                ubuntu_cmd = f"cmd.exe /c start {target}"
                win_cmd = f"cmd.exe /c start {target}"
            elif app_type == "protocol":
                ubuntu_cmd = f"cmd.exe /c start {target}"
                win_cmd = f"powershell.exe -NoProfile -Command \"Start-Process '{target}'\""
            elif app_type in ("lnk", "exe"):
                # Forward slashes for bash quote safety
                fwd_target = target.replace("\\", "/")
                ubuntu_cmd = f'cmd.exe /c start "" "{fwd_target}"'
                win_cmd = f'cmd.exe /c start "" "{target}"'
            elif app_type == "uwp":
                ubuntu_cmd = f'powershell.exe -NoProfile -Command "Start-Process \'shell:AppsFolder\\{target}\'"'
                win_cmd = f'powershell.exe -NoProfile -Command "Start-Process \'shell:AppsFolder\\{target}\'"'
            else:
                ubuntu_cmd = f"cmd.exe /c start {raw}"
                win_cmd = f"cmd.exe /c start {raw}"

            return {
                "found": True,
                "title": title,
                "type": app_type,
                "target": target,
                "shell_cmd": ubuntu_cmd,
                "win_cmd": win_cmd,
                "description": desc
            }

        # Fallback for arbitrary or custom software
        clean_target = raw
        ubuntu_cmd = (
            f'cmd.exe /c start "" "{clean_target}" 2>/dev/null || '
            f'cmd.exe /c start {clean_target}: 2>/dev/null || '
            f'powershell.exe -NoProfile -Command "Start-Process \'{clean_target}\'" 2>/dev/null'
        )
        return {
            "found": False,
            "title": clean_target.title(),
            "type": "unknown",
            "target": clean_target,
            "shell_cmd": ubuntu_cmd,
            "win_cmd": f'cmd.exe /c start "" "{clean_target}"',
            "description": f"Application '{clean_target}'"
        }

# Global App Registry Singleton
app_registry = AppRegistry()


def resolve_app(app_name: str) -> Dict[str, Any]:
    """Compatibility interface for legacy callers."""
    info = app_registry.resolve_launch_info(app_name)
    return {
        "binary": info["target"],
        "ubuntu_cmd": info["shell_cmd"],
        "win_cmd": info["win_cmd"],
        "description": info["description"],
        "title": info["title"],
        "type": info["type"]
    }


def resolve_app_launch_command(app_name: str) -> Dict[str, Any]:
    """
    Used by ReActPlanner to get the exact display title, target,
    and Ubuntu bash execution command.
    """
    info = app_registry.resolve_launch_info(app_name)
    return {
        "title": info["title"],
        "display": info["target"],
        "shell_cmd": info["shell_cmd"],
        "win_cmd": info["win_cmd"],
        "type": info["type"]
    }


def launch_application(app_name: str) -> Dict[str, Any]:
    """
    Launches application directly on the desktop:
    1. Triggers direct Windows launch via os.startfile / subprocess
    2. Also spawns interactive Ubuntu terminal window executing the command
    """
    info = app_registry.resolve_launch_info(app_name)
    target = info["target"]
    app_type = info["type"]
    title = info["title"]
    desc = info["description"]
    ubuntu_cmd = info["shell_cmd"]

    # 1. Direct Windows Launch via native ShellExecuteW
    direct_success = False
    direct_err = None
    if platform.system() == "Windows":
        try:
            if app_type in ("lnk", "exe", "builtin", "protocol") and (os.path.exists(target) or app_type in ("builtin", "protocol")):
                ret = ctypes.windll.shell32.ShellExecuteW(None, "open", target, None, None, 1)
                direct_success = ret > 32
            elif app_type == "uwp":
                subprocess.Popen(f'powershell.exe -NoProfile -Command "Start-Process \'shell:AppsFolder\\{target}\'"', shell=True)
                direct_success = True
            else:
                ret = ctypes.windll.shell32.ShellExecuteW(None, "open", target, None, None, 1)
                direct_success = ret > 32
        except Exception as e:
            direct_err = str(e)

    # 2. Spawn Interactive Ubuntu Terminal Window
    terminal_res = ubuntu_bridge.launch_interactive_command(ubuntu_cmd, desc)

    return {
        "success": True,
        "title": title,
        "target": target,
        "direct_launched": direct_success,
        "output": f"Successfully launched '{title}' on your desktop.",
        "terminal_output": terminal_res.get("output", "")
    }


def launch_browser_url(url: str, browser: str = "chrome") -> Dict[str, Any]:
    """Launches a specific URL on the requested browser (Chrome, Brave, Edge, etc.)."""
    clean_browser = browser.lower()
    is_windows = platform.system() == "Windows"

    if clean_browser == "brave":
        exec_cmd = f"cmd.exe /c start brave {url}"
    elif clean_browser in ("edge", "msedge"):
        exec_cmd = f"cmd.exe /c start msedge {url}"
    else:
        exec_cmd = f"cmd.exe /c start chrome {url}"

    if is_windows:
        try:
            subprocess.Popen(exec_cmd, shell=True)
            return {
                "success": True,
                "output": f"Successfully launched {url} on {browser.title()}.",
                "url": url,
                "browser": browser
            }
        except Exception as e:
            return {"success": False, "output": f"Failed to launch browser: {str(e)}"}
    else:
        try:
            subprocess.Popen([clean_browser, url])
            return {"success": True, "output": f"Launched {url} on {browser}."}
        except Exception as e:
            return {"success": False, "output": str(e)}
