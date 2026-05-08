"""Annotate diff entries with human-readable change descriptions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus


@dataclass
class AnnotatedEntry:
    """A diff entry paired with a descriptive annotation string."""

    entry: DiffEntry
    annotation: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"AnnotatedEntry({self.entry.key!r}, {self.annotation!r})"


def _describe(entry: DiffEntry) -> str:
    """Return a short human-readable description of a single diff entry."""
    if entry.status == DiffStatus.ADDED:
        preview = (entry.production_value or "")[:40]
        return f"Added in production (value: {preview!r})"
    if entry.status == DiffStatus.REMOVED:
        preview = (entry.staging_value or "")[:40]
        return f"Present in staging only (value: {preview!r})"
    if entry.status == DiffStatus.CHANGED:
        s = (entry.staging_value or "")[:20]
        p = (entry.production_value or "")[:20]
        return f"Value changed: {s!r} -> {p!r}"
    return "Identical in both environments"


def annotate(result: DiffResult, *, include_unchanged: bool = False) -> List[AnnotatedEntry]:
    """Return annotated entries for *result*.

    Args:
        result: The diff result to annotate.
        include_unchanged: When *True* unchanged entries are included too.

    Returns:
        A list of :class:`AnnotatedEntry` objects in the original key order.
    """
    out: List[AnnotatedEntry] = []
    for entry in result.entries:
        if entry.status == DiffStatus.UNCHANGED and not include_unchanged:
            continue
        out.append(AnnotatedEntry(entry=entry, annotation=_describe(entry)))
    return out


def annotation_summary(annotated: List[AnnotatedEntry]) -> Optional[str]:
    """Return a one-line summary sentence for a list of annotated entries.

    Returns *None* when the list is empty.
    """
    if not annotated:
        return None
    counts: dict[DiffStatus, int] = {}
    for ae in annotated:
        counts[ae.entry.status] = counts.get(ae.entry.status, 0) + 1
    parts = []
    if counts.get(DiffStatus.ADDED):
        parts.append(f"{counts[DiffStatus.ADDED]} added")
    if counts.get(DiffStatus.REMOVED):
        parts.append(f"{counts[DiffStatus.REMOVED]} removed")
    if counts.get(DiffStatus.CHANGED):
        parts.append(f"{counts[DiffStatus.CHANGED]} changed")
    if counts.get(DiffStatus.UNCHANGED):
        parts.append(f"{counts[DiffStatus.UNCHANGED]} unchanged")
    return ", ".join(parts) + "."
