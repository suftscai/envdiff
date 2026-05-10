"""comparator.py – compare two env dicts and produce a similarity report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set

from envdiff.differ import DiffResult, DiffStatus, diff_envs


@dataclass
class SimilarityReport:
    """High-level similarity metrics between two env sets."""

    total_keys: int
    shared_keys: int          # keys present in both files
    identical_keys: int       # keys present in both with the same value
    added_keys: int           # keys only in right (production)
    removed_keys: int         # keys only in left (staging)
    changed_keys: int         # keys in both but with different values
    similarity_pct: float     # identical / total_keys * 100
    jaccard_index: float      # |intersection| / |union|

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SimilarityReport(total={self.total_keys}, "
            f"identical={self.identical_keys}, "
            f"similarity={self.similarity_pct:.1f}%, "
            f"jaccard={self.jaccard_index:.3f})"
        )


def compare_envs(
    staging: Dict[str, str],
    production: Dict[str, str],
) -> SimilarityReport:
    """Compare two env dicts and return a :class:`SimilarityReport`."""
    result: DiffResult = diff_envs(staging, production)

    left_keys: Set[str] = set(staging)
    right_keys: Set[str] = set(production)
    union_size = len(left_keys | right_keys)
    intersection_size = len(left_keys & right_keys)

    added = sum(1 for e in result.entries if e.status == DiffStatus.ADDED)
    removed = sum(1 for e in result.entries if e.status == DiffStatus.REMOVED)
    changed = sum(1 for e in result.entries if e.status == DiffStatus.CHANGED)
    identical = sum(1 for e in result.entries if e.status == DiffStatus.UNCHANGED)

    total_keys = union_size
    similarity_pct = (identical / total_keys * 100) if total_keys else 100.0
    jaccard = (intersection_size / union_size) if union_size else 1.0

    return SimilarityReport(
        total_keys=total_keys,
        shared_keys=intersection_size,
        identical_keys=identical,
        added_keys=added,
        removed_keys=removed,
        changed_keys=changed,
        similarity_pct=round(similarity_pct, 2),
        jaccard_index=round(jaccard, 4),
    )


def format_comparison_text(report: SimilarityReport) -> str:
    """Return a human-readable summary of a :class:`SimilarityReport`."""
    lines = [
        f"Total keys : {report.total_keys}",
        f"Shared keys: {report.shared_keys}",
        f"Identical  : {report.identical_keys}",
        f"Added      : {report.added_keys}",
        f"Removed    : {report.removed_keys}",
        f"Changed    : {report.changed_keys}",
        f"Similarity : {report.similarity_pct:.1f}%",
        f"Jaccard    : {report.jaccard_index:.4f}",
    ]
    return "\n".join(lines)
