"""Text and colour formatting for diff results."""

from __future__ import annotations

from typing import Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.masker import mask_value

# ANSI colour codes
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def _format_entry_plain(
    entry: DiffEntry, *, mask_secrets: bool = False
) -> str:
    key = entry.key

    def _val(v: Optional[str]) -> str:
        if v is None:
            return "<missing>"
        return mask_value(key, v) if mask_secrets else v

    if entry.status == DiffStatus.ADDED:
        return f"+ {key}={_val(entry.production_value)}"
    if entry.status == DiffStatus.REMOVED:
        return f"- {key}={_val(entry.staging_value)}"
    if entry.status == DiffStatus.CHANGED:
        return (
            f"~ {key}: {_val(entry.staging_value)!r} "
            f"-> {_val(entry.production_value)!r}"
        )
    return f"  {key}={_val(entry.staging_value)}"


def _format_entry_color(
    entry: DiffEntry, *, mask_secrets: bool = False
) -> str:
    plain = _format_entry_plain(entry, mask_secrets=mask_secrets)
    if entry.status == DiffStatus.ADDED:
        return f"{_GREEN}{plain}{_RESET}"
    if entry.status == DiffStatus.REMOVED:
        return f"{_RED}{plain}{_RESET}"
    if entry.status == DiffStatus.CHANGED:
        return f"{_YELLOW}{plain}{_RESET}"
    return plain


def format_text(
    result: DiffResult,
    *,
    color: bool = False,
    show_unchanged: bool = False,
    mask_secrets: bool = False,
) -> str:
    """Render *result* as a human-readable string."""
    fmt = _format_entry_color if color else _format_entry_plain
    lines = []
    for entry in result.entries:
        if entry.status == DiffStatus.UNCHANGED and not show_unchanged:
            continue
        lines.append(fmt(entry, mask_secrets=mask_secrets))
    return "\n".join(lines)


def format_summary(result: DiffResult) -> str:
    """Return a one-line summary of counts."""
    s = result.summary
    return (
        f"added={s['added']}  removed={s['removed']}  "
        f"changed={s['changed']}  unchanged={s['unchanged']}"
    )
