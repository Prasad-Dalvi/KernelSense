"""
Ubuntu WSL Integration & External Execution Bridge for KernelSense
Provides direct interactive and non-interactive command execution inside Ubuntu Linux (WSL2).
"""

import subprocess
import platform
from typing import Dict, Any


class UbuntuBridge:
    def __init__(self, distro: str = "Ubuntu"):
        self.distro = distro
        self.is_windows = platform.system() == "Windows"

    def is_available(self) -> bool:
        """Checks if Ubuntu WSL is installed and reachable."""
        if not self.is_windows:
            return True
        try:
            res = subprocess.run(
                ["wsl.exe", "-d", self.distro, "--", "echo", "ok"],
                capture_output=True,
                text=True,
                timeout=3
            )
            return res.returncode == 0
        except Exception:
            return False

    def launch_interactive_command(self, app_cmd: str, description: str = "Application") -> Dict[str, Any]:
        """
        Spawns a full interactive Ubuntu Linux terminal window on the desktop,
        prints the banner, runs the specified command, and leaves the interactive shell open.
        """
        if not self.is_windows:
            subprocess.Popen([app_cmd], shell=True)
            return {"success": True, "output": f"Launched '{app_cmd}' natively on Linux desktop."}

        try:
            # Build interactive bash script with banner and exec bash
            bash_script = (
                f'echo "================================================="; '
                f'echo "  KernelSense Ubuntu Terminal Session"; '
                f'echo "  Target: {description}"; '
                f'echo "  Command: {app_cmd}"; '
                f'echo "================================================="; '
                f'{app_cmd}; '
                f'exec bash'
            )

            subprocess.Popen([
                "cmd.exe", "/c", "start",
                "wsl.exe", "-d", self.distro,
                "bash", "-c", bash_script
            ])
            return {
                "success": True,
                "output": f"Spawned interactive Ubuntu terminal window executing '{app_cmd}'."
            }
        except Exception as e:
            return {"success": False, "output": f"Failed to spawn interactive Ubuntu terminal: {str(e)}"}

    def run_command(self, command: str, timeout_sec: int = 10) -> Dict[str, Any]:
        """
        Executes a shell command inside Ubuntu non-interactively and captures live Linux stdout/stderr.
        """
        if not self.is_windows:
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout_sec)
            return {
                "success": res.returncode == 0,
                "output": res.stdout if res.returncode == 0 else res.stderr
            }

        try:
            res = subprocess.run(
                ["wsl.exe", "-d", self.distro, "--", "bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            out = res.stdout if res.returncode == 0 else (res.stderr or f"Exited with code {res.returncode}")
            return {
                "success": res.returncode == 0,
                "output": out.strip()
            }
        except Exception as e:
            return {"success": False, "output": f"Ubuntu execution error: {str(e)}"}


ubuntu_bridge = UbuntuBridge()
