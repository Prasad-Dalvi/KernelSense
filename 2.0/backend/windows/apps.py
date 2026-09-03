"""
Windows & External Ubuntu (WSL) Application & URL Execution Engine for KernelSense
Provides direct interactive desktop app spawning, URL launching, and Ubuntu terminal sessions.
"""

import os
import sys
import ctypes
import platform
import subprocess
from typing import Dict, Any, Optional

from ubuntu.bridge import ubuntu_bridge

APP_REGISTRY = {
    "calculator": {
        "binary": "calc.exe",
        "ubuntu_cmd": "calc.exe",
        "description": "Windows Calculator"
    },
    "calc": {
        "binary": "calc.exe",
        "ubuntu_cmd": "calc.exe",
        "description": "Windows Calculator"
    },
    "notepad": {
        "binary": "notepad.exe",
        "ubuntu_cmd": "notepad.exe",
        "description": "Notepad Text Editor"
    },
    "paint": {
        "binary": "mspaint.exe",
        "ubuntu_cmd": "mspaint.exe",
        "description": "Paint Application"
    },
    "mspaint": {
        "binary": "mspaint.exe",
        "ubuntu_cmd": "mspaint.exe",
        "description": "Paint Application"
    },
    "settings": {
        "binary": "control.exe",
        "ubuntu_cmd": "cmd.exe /c start ms-settings:",
        "description": "Windows Settings"
    },
    "task manager": {
        "binary": "taskmgr.exe",
        "ubuntu_cmd": "taskmgr.exe",
        "description": "Task Manager"
    },
    "taskmgr": {
        "binary": "taskmgr.exe",
        "ubuntu_cmd": "taskmgr.exe",
        "description": "Task Manager"
    },
    "brave": {
        "binary": "brave.exe",
        "ubuntu_cmd": "cmd.exe /c start brave",
        "description": "Brave Web Browser"
    },
    "chrome": {
        "binary": "chrome.exe",
        "ubuntu_cmd": "cmd.exe /c start chrome",
        "description": "Google Chrome Browser"
    },
    "edge": {
        "binary": "msedge.exe",
        "ubuntu_cmd": "cmd.exe /c start msedge",
        "description": "Microsoft Edge Browser"
    },
    "explorer": {
        "binary": "explorer.exe",
        "ubuntu_cmd": "explorer.exe",
        "description": "File Explorer"
    },
    "ubuntu": {
        "binary": "wsl.exe",
        "ubuntu_cmd": "echo 'Ubuntu Terminal Ready'; uname -a",
        "description": "Ubuntu Linux Terminal"
    },
    "wsl": {
        "binary": "wsl.exe",
        "ubuntu_cmd": "echo 'Ubuntu Terminal Ready'; uname -a",
        "description": "Ubuntu Linux Terminal"
    },
    "nano": {
        "binary": "wsl.exe",
        "ubuntu_cmd": "nano",
        "description": "Ubuntu Nano Text Editor"
    },
    "vim": {
        "binary": "wsl.exe",
        "ubuntu_cmd": "vim",
        "description": "Ubuntu Vim Text Editor"
    },
    "htop": {
        "binary": "wsl.exe",
        "ubuntu_cmd": "htop",
        "description": "Ubuntu Htop Monitor"
    },
    "python": {
        "binary": "python.exe",
        "ubuntu_cmd": "python3",
        "description": "Python Interactive Shell"
    },
    "terminal": {
        "binary": "wt.exe",
        "ubuntu_cmd": "echo 'Terminal session started.'",
        "description": "Terminal Console"
    }
}

def resolve_app(app_name: str) -> Dict[str, Any]:
    """Resolves an app name to its executable, Ubuntu command and description."""
    clean = app_name.strip().lower()
    
    if clean in APP_REGISTRY:
        return APP_REGISTRY[clean]
        
    for k, v in APP_REGISTRY.items():
        if k in clean or clean in k:
            return v
            
    return {
        "binary": clean if clean.endswith(".exe") else f"{clean}.exe",
        "ubuntu_cmd": clean,
        "description": f"Application '{app_name}'"
    }

def launch_application(app_name: str) -> Dict[str, Any]:
    """
    Launches application via the interactive Ubuntu Linux Terminal Bridge:
    1. Spawns visible interactive Ubuntu terminal on the desktop
    2. Runs target application command inside Ubuntu
    3. Keeps the terminal session interactive for user control
    """
    app_info = resolve_app(app_name)
    ubuntu_cmd = app_info.get("ubuntu_cmd", app_name)
    desc = app_info.get("description", app_name)
    
    return ubuntu_bridge.launch_interactive_command(ubuntu_cmd, desc)

def launch_browser_url(url: str, browser: str = "chrome") -> Dict[str, Any]:
    """
    Launches a specific URL on the requested browser (Chrome, Brave, Edge, etc.).
    """
    clean_browser = browser.lower()
    is_windows = platform.system() == "Windows"
    
    # Format Windows execution command
    if clean_browser == "brave":
        exec_cmd = f"cmd.exe /c start brave {url}"
    elif clean_browser == "edge" or clean_browser == "msedge":
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
