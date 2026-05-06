"""Generate structured report data from a DiffResult for JSON/YAML export."""

from __future__ import annotations

import json
from typing import Any

from envdiff.differ import DiffResult, DiffStatus


def _entry_to_dict(entry) -> dict[str, Any]:
    """Convert a single DiffEntry to a serialisable dictionary."""
    record: dict[str, Any] = {
        "key": entry.key,
        "status": entry.status.value,
    }
    if entry.status == DiffStatus.ADDED:
        record["production_value"] = entry.production_value
    elif entry.status == DiffStatus.REMOVED:
        record["staging_value"] = entry.staging_value
    elif entry.status == DiffStatus.CHANGED:
        record["staging_value"] = entry.staging_value
        record["production_value"] = entry.production_value
    return record


def build_report(result: DiffResult) -> dict[str, Any]:
    """Return a structured report dict from a DiffResult.

    The report contains:
    - summary counts per status
    - a list of individual diff entries
    """
    entries = [
        _entry_to_dict(e)
        for e in result.entries
        if e.status != DiffStatus.UNCHANGED
    ]

    summary = {
        "added": len(result.added()),
        "removed": len(result.removed()),
        "changed": len(result.changed()),
        "unchanged": len(result.unchanged()),
    }

    return {"summary": summary, "differences": entries}


def report_json(result: DiffResult, indent: int = 2) -> str:
    """Serialise a DiffResult to a JSON string."""
    return json.dumps(build_report(result), indent=indent)
