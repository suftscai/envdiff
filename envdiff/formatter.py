"""Output formatters for DiffResult."""

from typing import List

from envdiff.differ import DiffEntry, DiffResult, DiffStatus

_STATUS_SYMBOL = {
    DiffStatus.ADDED: "+",
    DiffStatus.REMOVED: "-",
    DiffStatus.CHANGED: "~",
    DiffStatus.UNCHANGED: " ",
}

_STATUS_COLOR = {
    DiffStatus.ADDED: "\033[32m",   # green
    DiffStatus.REMOVED: "\033[31m",  # red
    DiffStatus.CHANGED: "\033[33m",  # yellow
    DiffStatus.UNCHANGED: "",
}
_RESET = "\033[0m"


def _format_entry_plain(entry: DiffEntry) -> str:
    sym = _STATUS_SYMBOL[entry.status]
    if entry.status == DiffStatus.CHANGED:
        return f"{sym} {entry.key}: {entry.left_value!r} -> {entry.right_value!r}"
    value = entry.right_value if entry.status == DiffStatus.ADDED else entry.left_value
    return f"{sym} {entry.key}={value}"


def _format_entry_color(entry: DiffEntry) -> str:
    color = _STATUS_COLOR[entry.status]
    line = _format_entry_plain(entry)
    return f"{color}{line}{_RESET}" if color else line


def format_text(result: DiffResult, color: bool = False) -> str:
    """Render a DiffResult as a human-readable text block."""
    if not result.entries:
        return "No differences found."

    lines: List[str] = []
    fmt = _format_entry_color if color else _format_entry_plain
    for entry in result.entries:
        lines.append(fmt(entry))
    return "\n".join(lines)


def format_summary(result: DiffResult) -> str:
    """Return a one-line summary of the diff."""
    parts = []
    if result.added:
        parts.append(f"{len(result.added)} added")
    if result.removed:
        parts.append(f"{len(result.removed)} removed")
    if result.changed:
        parts.append(f"{len(result.changed)} changed")
    if not parts:
        return "Environments are identical."
    return "Diff: " + ", ".join(parts) + "."
