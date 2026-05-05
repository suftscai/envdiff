"""Text and summary formatters for DiffResult."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .differ import DiffEntry, DiffResult

from .differ import DiffStatus

# ANSI colour codes
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def _format_entry_plain(entry: "DiffEntry") -> str:
    if entry.status == DiffStatus.ADDED:
        return f"+ {entry.key}={entry.value_b}"
    if entry.status == DiffStatus.REMOVED:
        return f"- {entry.key}={entry.value_a}"
    if entry.status == DiffStatus.CHANGED:
        return f"~ {entry.key}: {entry.value_a!r} -> {entry.value_b!r}"
    return f"  {entry.key}={entry.value_a}"


def _format_entry_color(entry: "DiffEntry") -> str:
    plain = _format_entry_plain(entry)
    if entry.status == DiffStatus.ADDED:
        return f"{_GREEN}{plain}{_RESET}"
    if entry.status == DiffStatus.REMOVED:
        return f"{_RED}{plain}{_RESET}"
    if entry.status == DiffStatus.CHANGED:
        return f"{_YELLOW}{plain}{_RESET}"
    return plain


def format_text(
    result: "DiffResult",
    *,
    color: bool = True,
    show_unchanged: bool = False,
    label_a: str = "a",
    label_b: str = "b",
) -> str:
    """Return a multi-line diff string for *result*."""
    lines: list[str] = []
    if label_a or label_b:
        lines.append(f"--- {label_a}")
        lines.append(f"+++ {label_b}")

    fmt = _format_entry_color if color else _format_entry_plain

    for entry in result.entries:
        if entry.status == DiffStatus.UNCHANGED and not show_unchanged:
            continue
        lines.append(fmt(entry))

    return "\n".join(lines)


def format_summary(
    result: "DiffResult",
    *,
    label_a: str = "a",
    label_b: str = "b",
) -> str:
    """Return a one-line summary of the diff."""
    if result.is_identical():
        return f"{label_a} and {label_b} are identical."
    parts = []
    if result.n_added:
        parts.append(f"{result.n_added} added")
    if result.n_removed:
        parts.append(f"{result.n_removed} removed")
    if result.n_changed:
        parts.append(f"{result.n_changed} changed")
    summary = ", ".join(parts)
    return f"{label_a} vs {label_b}: {summary}."
