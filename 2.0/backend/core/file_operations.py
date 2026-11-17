"""Safe local file creation helpers for explicit assistant requests."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional


_CREATE_FILE_PATTERN = re.compile(
    r"^\s*(?:(?:please|can you|could you|would you)\s+)?"
    r"(?:create|make|touch|new)\s+"
    r"(?:(?:a|an|the)\s+)?(?:new\s+|empty\s+)?file"
    r"(?:\s+(?:named|called))?(?:\s+(?:at|in))?"
    r"(?:\s*[:=]\s*|\s+)?(.*?)\s*$",
    re.IGNORECASE,
)


def parse_file_creation_request(query: str) -> Optional[str]:
    """Return the requested path, or an empty string for a missing path."""
    match = _CREATE_FILE_PATTERN.match(query)
    if not match:
        return None

    target = match.group(1).strip()
    if len(target) >= 2 and target[0] == target[-1] and target[0] in {"'", '"'}:
        target = target[1:-1].strip()
    return target


def validate_file_target(file_path: str) -> Path:
    """Validate an absolute path whose parent directory already exists."""
    raw_path = file_path.strip()
    if not raw_path or any(ord(char) < 32 for char in raw_path):
        raise ValueError("Provide a valid absolute file path.")

    target = Path(raw_path).expanduser()
    if not target.is_absolute():
        raise ValueError("Use an absolute path, such as C:\\Users\\you\\Desktop\\notes.txt.")
    if target.name in {"", ".", ".."}:
        raise ValueError("The path must include a file name.")

    filename = target.name
    if os.name == "nt":
        if filename.endswith((" ", ".")) or ":" in filename:
            raise ValueError("The file name is not valid on Windows.")
        device_name = filename.split(".", 1)[0].upper()
        if (
            device_name in {"CON", "PRN", "AUX", "NUL"}
            or re.fullmatch(r"(?:COM|LPT)[1-9]", device_name)
        ):
            raise ValueError("That name is reserved by Windows.")

    try:
        parent = target.parent.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"The parent folder does not exist: {target.parent}") from exc
    if not parent.is_dir():
        raise ValueError(f"The parent path is not a folder: {parent}")

    return parent / filename


def create_empty_file(file_path: str) -> Path:
    """Create a new empty file without replacing an existing file."""
    target = validate_file_target(file_path)
    with target.open("xb"):
        pass
    return target
