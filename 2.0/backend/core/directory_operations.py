"""Bounded local directory listing for natural-language assistant requests."""

import os
import re
from pathlib import Path
from typing import Optional, Tuple

MAX_DIRECTORY_LISTING = 100
_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}
_LIST_REQUEST = re.compile(
    r"^\s*(?:please\s+)?(?:list|show|display)\s+"
    r"(?:(?:the\s+)?(?:top|first)\s+)?"
    r"(?:(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+)?"
    r"files?\s+(?:in|inside|from|under)\s+(?:the\s+)?(?:folder|directory)\s+"
    r"(?P<path>.+?)\s*[.!?]?\s*$",
    re.IGNORECASE,
)


def parse_directory_listing_request(query: str) -> Optional[Tuple[str, int]]:
    match = _LIST_REQUEST.match(query)
    if not match:
        return None

    raw_count = match.group("count")
    if raw_count is None:
        limit = 10
    elif raw_count.isdigit():
        limit = int(raw_count)
    else:
        limit = _NUMBER_WORDS[raw_count.lower()]

    if not 1 <= limit <= MAX_DIRECTORY_LISTING:
        raise ValueError(f"Choose a file count from 1 to {MAX_DIRECTORY_LISTING}.")

    path = match.group("path").strip()
    if len(path) >= 2 and path[0] == path[-1] and path[0] in "\"'":
        path = path[1:-1]
    return path, limit


def list_directory_files(path_value: str, limit: int) -> Tuple[Path, list[Path]]:
    if not 1 <= limit <= MAX_DIRECTORY_LISTING:
        raise ValueError(f"Choose a file count from 1 to {MAX_DIRECTORY_LISTING}.")

    directory = Path(path_value).expanduser()
    try:
        directory = directory.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Directory does not exist: {path_value}") from exc
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    with os.scandir(directory) as scanner:
        files = sorted(
            (Path(entry.path) for entry in scanner if entry.is_file(follow_symlinks=False)),
            key=lambda file_path: file_path.name.casefold(),
        )
    return directory, files[:limit]
