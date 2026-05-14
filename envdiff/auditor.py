"""Audit trail: record which keys changed between two snapshots over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class AuditEvent:
    key: str
    status: DiffStatus
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    label: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AuditEvent(key={self.key!r}, status={self.status.value}, "
            f"label={self.label!r})"
        )


@dataclass
class AuditReport:
    events: List[AuditEvent]
    label: str = ""

    @property
    def total(self) -> int:
        return len(self.events)

    @property
    def by_status(self) -> Dict[DiffStatus, List[AuditEvent]]:
        result: Dict[DiffStatus, List[AuditEvent]] = {}
        for event in self.events:
            result.setdefault(event.status, []).append(event)
        return result

    def keys_changed(self) -> List[str]:
        return [e.key for e in self.events if e.status == DiffStatus.CHANGED]

    def keys_added(self) -> List[str]:
        return [e.key for e in self.events if e.status == DiffStatus.ADDED]

    def keys_removed(self) -> List[str]:
        return [e.key for e in self.events if e.status == DiffStatus.REMOVED]


def build_audit(result: DiffResult, label: str = "") -> AuditReport:
    """Create an AuditReport from a DiffResult, excluding UNCHANGED entries."""
    events: List[AuditEvent] = [
        AuditEvent(
            key=entry.key,
            status=entry.status,
            old_value=entry.staging_value,
            new_value=entry.production_value,
            label=label,
        )
        for entry in result.entries
        if entry.status != DiffStatus.UNCHANGED
    ]
    return AuditReport(events=events, label=label)


def format_audit_text(report: AuditReport) -> str:
    """Return a human-readable audit trail string."""
    if not report.events:
        return "No audit events recorded."
    lines = []
    if report.label:
        lines.append(f"Audit: {report.label}")
    for event in sorted(report.events, key=lambda e: e.key):
        lines.append(
            f"  [{event.status.value.upper():8s}] {event.key}  "
            f"({event.old_value!r} -> {event.new_value!r})  @ {event.timestamp}"
        )
    return "\n".join(lines)
