"""Tests for envdiff.sorter."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.sorter import group_by_status, sort_entries


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def entries() -> list[DiffEntry]:
    return [
        DiffEntry("ZEBRA", DiffStatus.ADDED, None, "z"),
        DiffEntry("APPLE", DiffStatus.REMOVED, "a", None),
        DiffEntry("MANGO", DiffStatus.CHANGED, "old", "new"),
        DiffEntry("BANANA", DiffStatus.UNCHANGED, "b", "b"),
        DiffEntry("CHERRY", DiffStatus.ADDED, None, "c"),
    ]


@pytest.fixture()
def diff_result(entries) -> DiffResult:
    return DiffResult(entries)


# ---------------------------------------------------------------------------
# sort_entries
# ---------------------------------------------------------------------------

def test_sort_by_name_ascending(entries):
    result = sort_entries(entries, key="name")
    names = [e.name for e in result]
    assert names == sorted(names)


def test_sort_by_name_descending(entries):
    result = sort_entries(entries, key="name", reverse=True)
    names = [e.name for e in result]
    assert names == sorted(names, reverse=True)


def test_sort_by_status(entries):
    result = sort_entries(entries, key="status")
    statuses = [e.status.value for e in result]
    assert statuses == sorted(statuses)


def test_sort_unsupported_key_raises(entries):
    with pytest.raises(ValueError, match="Unsupported sort key"):
        sort_entries(entries, key="nonexistent")


def test_sort_returns_new_list(entries):
    result = sort_entries(entries)
    assert result is not entries


# ---------------------------------------------------------------------------
# group_by_status
# ---------------------------------------------------------------------------

def test_group_excludes_unchanged_by_default(diff_result):
    groups = group_by_status(diff_result)
    assert DiffStatus.UNCHANGED not in groups


def test_group_includes_unchanged_when_requested(diff_result):
    groups = group_by_status(diff_result, include_unchanged=True)
    assert DiffStatus.UNCHANGED in groups


def test_group_added_entries(diff_result):
    groups = group_by_status(diff_result)
    added_names = [e.name for e in groups[DiffStatus.ADDED]]
    assert added_names == sorted(added_names)
    assert set(added_names) == {"CHERRY", "ZEBRA"}


def test_group_removed_entries(diff_result):
    groups = group_by_status(diff_result)
    assert len(groups[DiffStatus.REMOVED]) == 1
    assert groups[DiffStatus.REMOVED][0].name == "APPLE"


def test_group_changed_entries(diff_result):
    groups = group_by_status(diff_result)
    assert len(groups[DiffStatus.CHANGED]) == 1
    assert groups[DiffStatus.CHANGED][0].name == "MANGO"
