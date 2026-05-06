"""Utilities for sorting and grouping DiffEntry results."""

from __future__ import annotations

from typing import Iterable, List

from envdiff.differ import DiffEntry, DiffResult, DiffStatus


def sort_entries(
    entries: Iterable[DiffEntry],
    *,
    key: str = "name",
    reverse: bool = False,
) -> List[DiffEntry]:
    """Return a sorted list of DiffEntry objects.

    Args:
        entries: Iterable of DiffEntry objects to sort.
        key: Attribute to sort by.  Supported values: ``"name"`` (default),
            ``"status"``.
        reverse: If ``True``, sort in descending order.

    Returns:
        A new list of DiffEntry objects in the requested order.

    Raises:
        ValueError: If *key* is not a supported sort key.
    """
    supported = {"name", "status"}
    if key not in supported:
        raise ValueError(f"Unsupported sort key {key!r}. Choose from {supported}.")

    return sorted(entries, key=lambda e: getattr(e, key).value if key == "status" else getattr(e, key), reverse=reverse)


def group_by_status(
    result: DiffResult,
    *,
    include_unchanged: bool = False,
) -> dict[DiffStatus, List[DiffEntry]]:
    """Group entries in a DiffResult by their DiffStatus.

    Args:
        result: A :class:`~envdiff.differ.DiffResult` to group.
        include_unchanged: When ``False`` (default) UNCHANGED entries are
            omitted from the output.

    Returns:
        A dict mapping each :class:`~envdiff.differ.DiffStatus` that has at
        least one entry to a sorted list of matching :class:`~envdiff.differ.DiffEntry`
        objects.
    """
    groups: dict[DiffStatus, List[DiffEntry]] = {}
    for entry in result.entries:
        if entry.status == DiffStatus.UNCHANGED and not include_unchanged:
            continue
        groups.setdefault(entry.status, []).append(entry)

    # Sort each group by name for deterministic output.
    for status in groups:
        groups[status] = sort_entries(groups[status], key="name")

    return groups
