"""Compute statistical change metrics from a DiffResult."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class ChangeStats:
    """Aggregated statistics derived from a DiffResult."""

    total: int
    added: int
    removed: int
    changed: int
    unchanged: int
    change_ratio: float  # (added + removed + changed) / total, 0.0 if total == 0
    churn_score: float   # weighted: removed*1.5 + changed*1.0 + added*0.5

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ChangeStats(total={self.total}, added={self.added}, "
            f"removed={self.removed}, changed={self.changed}, "
            f"unchanged={self.unchanged}, "
            f"change_ratio={self.change_ratio:.2f}, "
            f"churn_score={self.churn_score:.2f})"
        )


def compute_stats(result: DiffResult) -> ChangeStats:
    """Return a :class:`ChangeStats` computed from *result*."""
    counts = {s: 0 for s in DiffStatus}
    for entry in result.entries:
        counts[entry.status] += 1

    added = counts[DiffStatus.ADDED]
    removed = counts[DiffStatus.REMOVED]
    changed = counts[DiffStatus.CHANGED]
    unchanged = counts[DiffStatus.UNCHANGED]
    total = added + removed + changed + unchanged

    change_ratio = (added + removed + changed) / total if total else 0.0
    churn_score = removed * 1.5 + changed * 1.0 + added * 0.5

    return ChangeStats(
        total=total,
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
        change_ratio=change_ratio,
        churn_score=churn_score,
    )


def format_stats_text(stats: ChangeStats, label: Optional[str] = None) -> str:
    """Return a human-readable summary of *stats*."""
    header = f"Change Stats — {label}" if label else "Change Stats"
    lines = [
        header,
        "-" * len(header),
        f"  Total keys   : {stats.total}",
        f"  Added        : {stats.added}",
        f"  Removed      : {stats.removed}",
        f"  Changed      : {stats.changed}",
        f"  Unchanged    : {stats.unchanged}",
        f"  Change ratio : {stats.change_ratio:.1%}",
        f"  Churn score  : {stats.churn_score:.1f}",
    ]
    return "\n".join(lines)
