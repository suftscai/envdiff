"""Score the divergence between two environment variable sets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class DivergenceScore:
    """Numeric summary of how different two env sets are."""

    added: int
    removed: int
    changed: int
    unchanged: int
    total: int
    score: float  # 0.0 (identical) … 1.0 (completely different)
    grade: str    # A / B / C / D / F

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DivergenceScore(score={self.score:.2f}, grade={self.grade!r}, "
            f"added={self.added}, removed={self.removed}, changed={self.changed})"
        )


def _grade(score: float) -> str:
    """Map a 0-1 divergence score to a letter grade."""
    if score == 0.0:
        return "A"
    if score < 0.1:
        return "B"
    if score < 0.25:
        return "C"
    if score < 0.5:
        return "D"
    return "F"


def score_diff(result: DiffResult, weight_changed: float = 0.5) -> DivergenceScore:
    """Compute a divergence score from a :class:`DiffResult`.

    *weight_changed* controls how much a changed value counts relative to a
    fully added/removed key (default 0.5 — half as severe).

    The raw score is::

        (added + removed + changed * weight) / total_keys

    clamped to [0, 1].
    """
    if weight_changed < 0 or weight_changed > 1:
        raise ValueError("weight_changed must be between 0 and 1")

    entries = result.entries
    added = sum(1 for e in entries if e.status is DiffStatus.ADDED)
    removed = sum(1 for e in entries if e.status is DiffStatus.REMOVED)
    changed = sum(1 for e in entries if e.status is DiffStatus.CHANGED)
    unchanged = sum(1 for e in entries if e.status is DiffStatus.UNCHANGED)
    total = len(entries)

    if total == 0:
        raw = 0.0
    else:
        raw = (added + removed + changed * weight_changed) / total

    score = min(1.0, raw)
    return DivergenceScore(
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
        total=total,
        score=round(score, 4),
        grade=_grade(score),
    )
