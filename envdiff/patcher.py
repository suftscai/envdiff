"""Apply a set of env-var changes to produce a patched env dict."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus


@dataclass
class PatchResult:
    """Outcome of applying a diff to a base environment."""

    patched: Dict[str, str]
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PatchResult(applied={len(self.applied)}, "
            f"skipped={len(self.skipped)}, keys={len(self.patched)})"
        )


def patch_env(
    base: Dict[str, str],
    diff: DiffResult,
    *,
    statuses: Optional[List[DiffStatus]] = None,
    dry_run: bool = False,
) -> PatchResult:
    """Return a new env dict with *diff* applied on top of *base*.

    Parameters
    ----------
    base:
        The environment to patch (typically the staging env).
    diff:
        A :class:`~envdiff.differ.DiffResult` produced by comparing two envs.
    statuses:
        Limit which change types are applied.  Defaults to
        ``[ADDED, REMOVED, CHANGED]`` (i.e. everything except UNCHANGED).
    dry_run:
        When *True* the patched dict is returned but *base* is never mutated
        (it is never mutated regardless; a copy is always made).
    """
    if statuses is None:
        statuses = [DiffStatus.ADDED, DiffStatus.REMOVED, DiffStatus.CHANGED]

    result: Dict[str, str] = dict(base)
    applied: List[str] = []
    skipped: List[str] = []

    for entry in diff.entries:
        if entry.status not in statuses:
            skipped.append(entry.key)
            continue

        if entry.status == DiffStatus.REMOVED:
            result.pop(entry.key, None)
        else:
            # ADDED or CHANGED — production value wins
            if entry.production_value is not None:
                result[entry.key] = entry.production_value

        applied.append(entry.key)

    return PatchResult(patched=result, applied=applied, skipped=skipped)
