"""Restricted read-only console operations for the local web UI."""

import os
import shlex
import subprocess
from pathlib import Path
from typing import Optional

MAX_DIRECTORY_ENTRIES = 100
MAX_OUTPUT_CHARS = 16000
SYSTEM_COMMANDS = {"ipconfig", "systeminfo", "tasklist", "whoami"}
SHELL_OPERATORS = set("\r\n;&|<>")


def _tokens(command: str) -> list[str]:
    if not command.strip():
        raise ValueError("Enter a read-only command. Type `help` for the supported commands.")
    if any(char in SHELL_OPERATORS for char in command):
        raise ValueError("Shell operators and command chaining are not supported.")
    try:
        tokens = shlex.split(command, posix=False)
    except ValueError as exc:
        raise ValueError("Could not parse the command. Put paths with spaces in double quotes.") from exc
    return [
        token[1:-1] if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'" else token
        for token in tokens
    ]


def _resolve_directory(path_value: Optional[str], base: Optional[Path] = None) -> Path:
    path = Path(path_value or (str(base) if base else os.getcwd())).expanduser()
    if not path.is_absolute() and base:
        path = base / path
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Directory does not exist: {path_value or path}") from exc
    if not resolved.is_dir():
        raise ValueError(f"Not a directory: {resolved}")
    return resolved


def run_read_only_command(command: str, cwd: Optional[str] = None) -> dict:
    """Run one allowlisted directory or system-information operation without a shell."""
    if len(command) > 2000:
        raise ValueError("Command is too long.")

    working_directory = _resolve_directory(cwd)
    tokens = _tokens(command)
    name = tokens[0].lower()
    args = tokens[1:]

    if name == "help":
        if args:
            raise ValueError("`help` does not accept arguments.")
        output = "Supported: help, pwd, cd <folder>, dir [folder] [--limit N], ls [folder], whoami, ipconfig, systeminfo, tasklist"
        return {"success": True, "cwd": str(working_directory), "output": output}

    if name == "pwd":
        if args:
            raise ValueError("`pwd` does not accept arguments.")
        return {"success": True, "cwd": str(working_directory), "output": str(working_directory)}

    if name == "cd":
        if len(args) > 1:
            raise ValueError("Usage: cd [folder]")
        destination = _resolve_directory(args[0] if args else None, working_directory)
        return {"success": True, "cwd": str(destination), "output": str(destination)}

    if name in {"dir", "ls"}:
        limit = MAX_DIRECTORY_ENTRIES
        path_args = []
        index = 0
        while index < len(args):
            if args[index].lower() == "--limit":
                if index + 1 >= len(args):
                    raise ValueError("Usage: dir [folder] [--limit N]")
                try:
                    limit = int(args[index + 1])
                except ValueError as exc:
                    raise ValueError("Directory limit must be a number from 1 to 100.") from exc
                if not 1 <= limit <= MAX_DIRECTORY_ENTRIES:
                    raise ValueError("Directory limit must be from 1 to 100.")
                index += 2
                continue
            path_args.append(args[index])
            index += 1
        if len(path_args) > 1:
            raise ValueError("Use quotes around directory paths that contain spaces.")

        directory = _resolve_directory(path_args[0] if path_args else None, working_directory)
        with os.scandir(directory) as scanner:
            entries = sorted(
                scanner,
                key=lambda entry: (not entry.is_dir(follow_symlinks=False), entry.name.casefold()),
            )
        shown = entries[:limit]
        lines = [
            f"<DIR>  {entry.name}" if entry.is_dir(follow_symlinks=False) else f"       {entry.name}"
            for entry in shown
        ]
        if len(entries) > len(shown):
            lines.append(f"... showing {len(shown)} of {len(entries)} entries")
        output = "\n".join(lines) if lines else "Directory is empty."
        return {"success": True, "cwd": str(working_directory), "output": output}

    if name in SYSTEM_COMMANDS:
        if args:
            raise ValueError(f"`{name}` does not accept arguments.")
        try:
            result = subprocess.run(
                [name],
                cwd=str(working_directory),
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"`{name}` timed out after 15 seconds.") from exc
        output = (result.stdout or result.stderr or "").strip()
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n... output truncated"
        return {
            "success": result.returncode == 0,
            "cwd": str(working_directory),
            "output": output or f"{name} exited with code {result.returncode}.",
        }

    raise ValueError(
        f"Unsupported command: {tokens[0]}. Type `help` to see the read-only commands."
    )
