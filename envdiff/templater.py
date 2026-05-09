"""Generate .env template files from a diff result or parsed env dict.

A template replaces concrete values with placeholder comments so the file
can be committed safely and filled in per-environment.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from envdiff.differ import DiffResult, DiffStatus

__all__ = ["env_to_template", "template_from_diff"]

_PLACEHOLDER = "<FILL_IN>"
_SENSITIVE_PLACEHOLDER = "<SECRET>"

# Keys that should receive the secret placeholder
_SENSITIVE_PATTERNS = ("SECRET", "PASSWORD", "PASSWD", "TOKEN", "KEY", "PRIVATE", "CREDENTIAL")


def _is_sensitive(key: str) -> bool:
    upper = key.upper()
    return any(pat in upper for pat in _SENSITIVE_PATTERNS)


def _placeholder(key: str) -> str:
    return _SENSITIVE_PLACEHOLDER if _is_sensitive(key) else _PLACEHOLDER


def env_to_template(
    env: Dict[str, str],
    *,
    include_values: bool = False,
    header: Optional[str] = None,
) -> str:
    """Convert a parsed env dict into a template string.

    Args:
        env: Mapping of key -> value.
        include_values: When True, keep original values as inline comments.
        header: Optional comment block prepended to the output.

    Returns:
        A string suitable for writing as a ``.env.template`` file.
    """
    lines: list[str] = []
    if header:
        for line in header.splitlines():
            lines.append(f"# {line}" if not line.startswith("#") else line)
        lines.append("")

    for key in sorted(env):
        ph = _placeholder(key)
        if include_values:
            original = env[key]
            lines.append(f"{key}={ph}  # was: {original}")
        else:
            lines.append(f"{key}={ph}")

    return "\n".join(lines) + "\n"


def template_from_diff(
    result: DiffResult,
    *,
    statuses: Optional[Iterable[DiffStatus]] = None,
    include_values: bool = False,
) -> str:
    """Build a template from a :class:`DiffResult`.

    Only entries whose status is in *statuses* are included.  Defaults to
    ADDED, CHANGED, and REMOVED (i.e. everything except UNCHANGED).
    """
    if statuses is None:
        statuses = {DiffStatus.ADDED, DiffStatus.CHANGED, DiffStatus.REMOVED}
    else:
        statuses = set(statuses)

    lines: list[str] = []
    for entry in sorted(result.entries, key=lambda e: e.key):
        if entry.status not in statuses:
            continue
        ph = _placeholder(entry.key)
        comment = f"  # [{entry.status.value}]"
        if include_values and entry.staging_value is not None:
            comment += f" staging: {entry.staging_value}"
        lines.append(f"{entry.key}={ph}{comment}")

    return "\n".join(lines) + "\n" if lines else ""
