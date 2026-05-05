"""Parser for .env files and environment variable configs."""

import re
from pathlib import Path
from typing import Dict, Optional


ENV_LINE_PATTERN = re.compile(
    r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$'
)


def parse_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs.

    Supports:
    - KEY=VALUE
    - export KEY=VALUE
    - Quoted values (single and double quotes)
    - Inline comments (# ...)
    - Blank lines and full-line comments are ignored

    Args:
        path: Path to the .env file.

    Returns:
        Dictionary of environment variable names to their string values.

    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(f"Env file not found: {path}")

    result: Dict[str, str] = {}

    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            # Skip blank lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            match = ENV_LINE_PATTERN.match(line)
            if not match:
                continue

            key, value = match.group(1), match.group(2)
            value = _strip_inline_comment(value)
            value = _unquote(value)
            result[key] = value

    return result


def _strip_inline_comment(value: str) -> str:
    """Remove inline comment from a value string."""
    # Only strip if not inside quotes
    if value and value[0] not in ('"', "'"):
        comment_idx = value.find(" #")
        if comment_idx != -1:
            value = value[:comment_idx]
    return value.strip()


def _unquote(value: str) -> str:
    """Strip surrounding single or double quotes from a value."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or \
           (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value
