"""Snapshot support: save and load environment diff results to/from JSON files."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from envdiff.differ import DiffEntry, DiffResult, DiffStatus

_VERSION = 1


def save_snapshot(result: DiffResult, path: str, label: str = "") -> None:
    """Persist a DiffResult to *path* as a JSON snapshot."""
    data: dict[str, Any] = {
        "version": _VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "entries": [
            {
                "key": e.key,
                "status": e.status.value,
                "left": e.left,
                "right": e.right,
            }
            for e in result.entries
        ],
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_snapshot(path: str) -> DiffResult:
    """Reconstruct a DiffResult from a previously saved snapshot file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if data.get("version") != _VERSION:
        raise ValueError(
            f"Unsupported snapshot version: {data.get('version')!r}. "
            f"Expected {_VERSION}."
        )

    entries = [
        DiffEntry(
            key=e["key"],
            status=DiffStatus(e["status"]),
            left=e["left"],
            right=e["right"],
        )
        for e in data["entries"]
    ]
    return DiffResult(entries=entries)


def snapshot_metadata(path: str) -> dict[str, Any]:
    """Return the metadata fields (version, created_at, label) without loading entries."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {
        "version": data.get("version"),
        "created_at": data.get("created_at"),
        "label": data.get("label", ""),
        "entry_count": len(data.get("entries", [])),
    }
