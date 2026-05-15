"""Tests for envdiff.grouper."""

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.grouper import GroupReport, PrefixGroup, group_by_prefix


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def result() -> DiffResult:
    entries = [
        DiffEntry("DB_HOST", DiffStatus.CHANGED, "localhost", "db.prod"),
        DiffEntry("DB_PORT", DiffStatus.UNCHANGED, "5432", "5432"),
        DiffEntry("AWS_KEY", DiffStatus.ADDED, None, "AKIAIOSFODNN7"),
        DiffEntry("AWS_SECRET", DiffStatus.ADDED, None, "wJalrXUtnFEMI"),
        DiffEntry("APP_DEBUG", DiffStatus.REMOVED, "true", None),
        DiffEntry("STANDALONE", DiffStatus.CHANGED, "old", "new"),
    ]
    return DiffResult(entries=entries)


# ---------------------------------------------------------------------------
# GroupReport / PrefixGroup basics
# ---------------------------------------------------------------------------


def test_group_report_total(result):
    report = group_by_prefix(result)
    # UNCHANGED excluded by default; 5 changed/added/removed entries
    assert report.total == 5


def test_group_report_returns_group_report(result):
    report = group_by_prefix(result)
    assert isinstance(report, GroupReport)


def test_prefix_group_is_prefix_group(result):
    report = group_by_prefix(result)
    for group in report.groups.values():
        assert isinstance(group, PrefixGroup)


# ---------------------------------------------------------------------------
# Auto-prefix detection
# ---------------------------------------------------------------------------


def test_auto_prefix_groups_db(result):
    report = group_by_prefix(result)
    assert "DB" in report.groups
    assert report.groups["DB"].total == 1  # DB_PORT is UNCHANGED → excluded


def test_auto_prefix_groups_aws(result):
    report = group_by_prefix(result)
    assert "AWS" in report.groups
    assert report.groups["AWS"].total == 2


def test_auto_prefix_groups_app(result):
    report = group_by_prefix(result)
    assert "APP" in report.groups
    assert report.groups["APP"].total == 1


def test_key_without_separator_goes_to_ungrouped(result):
    report = group_by_prefix(result)
    keys = [e.key for e in report.ungrouped]
    assert "STANDALONE" in keys


# ---------------------------------------------------------------------------
# include_unchanged flag
# ---------------------------------------------------------------------------


def test_include_unchanged_adds_db_port(result):
    report = group_by_prefix(result, include_unchanged=True)
    assert report.groups["DB"].total == 2  # DB_HOST + DB_PORT


def test_include_unchanged_increases_total(result):
    without = group_by_prefix(result, include_unchanged=False)
    with_ = group_by_prefix(result, include_unchanged=True)
    assert with_.total > without.total


# ---------------------------------------------------------------------------
# Explicit prefixes
# ---------------------------------------------------------------------------


def test_explicit_prefix_filters_to_aws(result):
    report = group_by_prefix(result, prefixes=["AWS"])
    assert "AWS" in report.groups
    assert "DB" not in report.groups


def test_explicit_prefix_non_matching_goes_to_ungrouped(result):
    report = group_by_prefix(result, prefixes=["AWS"])
    ungrouped_keys = {e.key for e in report.ungrouped}
    assert "DB_HOST" in ungrouped_keys
    assert "APP_DEBUG" in ungrouped_keys


def test_explicit_prefix_case_insensitive(result):
    report = group_by_prefix(result, prefixes=["aws"])
    assert "AWS" in report.groups


# ---------------------------------------------------------------------------
# GroupReport.get helper
# ---------------------------------------------------------------------------


def test_get_returns_group(result):
    report = group_by_prefix(result)
    grp = report.get("aws")
    assert grp is not None
    assert grp.prefix == "AWS"


def test_get_missing_prefix_returns_none(result):
    report = group_by_prefix(result)
    assert report.get("NONEXISTENT") is None
