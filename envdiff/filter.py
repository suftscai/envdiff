"""Filter DiffResult entries by status, key pattern, or prefix."""

from __future__ import annotations

import fnmatch
import re
from typing import Iterable, Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus


def filter_by_status(
    result: DiffResult, statuses: Iterable[DiffStatus]
) -> DiffResult:
    """Return a new DiffResult keeping only entries whose status is in *statuses*."""
    allowed = set(statuses)
    kept = [e for e in result.entries if e.status in allowed]
    return DiffResult(entries=kept)


def filter_by_prefix(result: DiffResult, prefix: str) -> DiffResult:
    """Return entries whose key starts with *prefix* (case-sensitive)."""
    kept = [e for e in result.entries if e.key.startswith(prefix)]
    return DiffResult(entries=kept)


def filter_by_pattern(result: DiffResult, pattern: str) -> DiffResult:
    """Return entries whose key matches a Unix shell-style wildcard *pattern*."""
    kept = [e for e in result.entries if fnmatch.fnmatch(e.key, pattern)]
    return DiffResult(entries=kept)


def filter_by_regex(result: DiffResult, regex: str) -> DiffResult:
    """Return entries whose key matches the regular expression *regex*."""
    compiled = re.compile(regex)
    kept = [e for e in result.entries if compiled.search(e.key)]
    return DiffResult(entries=kept)


def exclude_unchanged(result: DiffResult) -> DiffResult:
    """Convenience: drop UNCHANGED entries."""
    return filter_by_status(
        result,
        [DiffStatus.ADDED, DiffStatus.REMOVED, DiffStatus.CHANGED],
    )
