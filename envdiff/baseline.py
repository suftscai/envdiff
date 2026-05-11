"""Baseline comparison: compare current env diff against a saved snapshot baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.snapshot import load_snapshot


@dataclass
class BaselineDelta:
    """Describes a change between a baseline snapshot and the current diff."""

    key: str
    baseline_status: Optional[DiffStatus]
    current_status: Optional[DiffStatus]
    baseline_staging: Optional[str]
    baseline_production: Optional[str]
    current_staging: Optional[str]
    current_production: Optional[str]

    @property
    def is_new(self) -> bool:
        """Key did not exist in the baseline."""
        return self.baseline_status is None

    @property
    def is_resolved(self) -> bool:
        """Key existed in baseline but is now unchanged."""
        return (
            self.baseline_status is not None
            and self.baseline_status != DiffStatus.UNCHANGED
            and self.current_status == DiffStatus.UNCHANGED
        )

    @property
    def is_regressed(self) -> bool:
        """Key was unchanged in baseline but now differs."""
        return (
            self.baseline_status == DiffStatus.UNCHANGED
            and self.current_status != DiffStatus.UNCHANGED
        )


@dataclass
class BaselineReport:
    """Full report comparing a baseline snapshot to the current diff result."""

    baseline_label: str
    deltas: List[BaselineDelta]

    @property
    def new_issues(self) -> List[BaselineDelta]:
        return [d for d in self.deltas if d.is_new]

    @property
    def resolved_issues(self) -> List[BaselineDelta]:
        return [d for d in self.deltas if d.is_resolved]

    @property
    def regressions(self) -> List[BaselineDelta]:
        return [d for d in self.deltas if d.is_regressed]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"BaselineReport(label={self.baseline_label!r}, "
            f"new={len(self.new_issues)}, resolved={len(self.resolved_issues)}, "
            f"regressions={len(self.regressions)})"
        )


def compare_to_baseline(current: DiffResult, snapshot_path: str) -> BaselineReport:
    """Compare *current* DiffResult against a saved snapshot baseline."""
    snapshot = load_snapshot(snapshot_path)
    label: str = snapshot.get("label", snapshot_path)
    baseline_entries: List[dict] = snapshot.get("differences", [])

    baseline_map: dict[str, dict] = {e["key"]: e for e in baseline_entries}
    current_map: dict[str, DiffEntry] = {e.key: e for e in current.entries}

    all_keys = set(baseline_map) | set(current_map)
    deltas: List[BaselineDelta] = []

    for key in sorted(all_keys):
        b = baseline_map.get(key)
        c = current_map.get(key)
        deltas.append(
            BaselineDelta(
                key=key,
                baseline_status=DiffStatus(b["status"]) if b else None,
                current_status=c.status if c else None,
                baseline_staging=b.get("staging") if b else None,
                baseline_production=b.get("production") if b else None,
                current_staging=c.staging if c else None,
                current_production=c.production if c else None,
            )
        )

    return BaselineReport(baseline_label=label, deltas=deltas)
