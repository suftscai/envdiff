"""Summarizer: produce human-readable summary statistics from a DiffResult."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class EnvSummary:
    """Aggregated statistics for a diff result."""

    total: int
    added: int
    removed: int
    changed: int
    unchanged: int
    staging_only: int
    production_only: int
    change_rate: float  # fraction of non-unchanged keys that differ

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EnvSummary(total={self.total}, added={self.added}, "
            f"removed={self.removed}, changed={self.changed}, "
            f"unchanged={self.unchanged}, change_rate={self.change_rate:.2%})"
        )


def summarize(result: DiffResult) -> EnvSummary:
    """Compute summary statistics from a DiffResult."""
    entries = result.entries

    added = sum(1 for e in entries if e.status == DiffStatus.ADDED)
    removed = sum(1 for e in entries if e.status == DiffStatus.REMOVED)
    changed = sum(1 for e in entries if e.status == DiffStatus.CHANGED)
    unchanged = sum(1 for e in entries if e.status == DiffStatus.UNCHANGED)
    total = len(entries)

    differing = added + removed + changed
    change_rate = differing / total if total > 0 else 0.0

    return EnvSummary(
        total=total,
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
        staging_only=removed,
        production_only=added,
        change_rate=change_rate,
    )


def format_summary_text(summary: EnvSummary, label: Optional[str] = None) -> str:
    """Render an EnvSummary as a plain-text block."""
    header = f"=== Env Summary{'  [' + label + ']' if label else ''} ==="
    lines = [
        header,
        f"  Total keys   : {summary.total}",
        f"  Added        : {summary.added}",
        f"  Removed      : {summary.removed}",
        f"  Changed      : {summary.changed}",
        f"  Unchanged    : {summary.unchanged}",
        f"  Change rate  : {summary.change_rate:.1%}",
    ]
    return "\n".join(lines)
