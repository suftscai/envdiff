"""Tests for envdiff.summarizer."""

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.summarizer import EnvSummary, format_summary_text, summarize


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _entry(key: str, status: DiffStatus) -> DiffEntry:
    return DiffEntry(key=key, staging_value="a", production_value="b", status=status)


@pytest.fixture()
def mixed_result() -> DiffResult:
    entries = [
        _entry("ADDED_KEY", DiffStatus.ADDED),
        _entry("REMOVED_KEY", DiffStatus.REMOVED),
        _entry("CHANGED_KEY", DiffStatus.CHANGED),
        _entry("SAME_KEY", DiffStatus.UNCHANGED),
        _entry("SAME_KEY2", DiffStatus.UNCHANGED),
    ]
    return DiffResult(entries=entries)


@pytest.fixture()
def empty_result() -> DiffResult:
    return DiffResult(entries=[])


# ---------------------------------------------------------------------------
# summarize()
# ---------------------------------------------------------------------------


def test_total_count(mixed_result):
    s = summarize(mixed_result)
    assert s.total == 5


def test_added_count(mixed_result):
    assert summarize(mixed_result).added == 1


def test_removed_count(mixed_result):
    assert summarize(mixed_result).removed == 1


def test_changed_count(mixed_result):
    assert summarize(mixed_result).changed == 1


def test_unchanged_count(mixed_result):
    assert summarize(mixed_result).unchanged == 2


def test_staging_only_equals_removed(mixed_result):
    s = summarize(mixed_result)
    assert s.staging_only == s.removed


def test_production_only_equals_added(mixed_result):
    s = summarize(mixed_result)
    assert s.production_only == s.added


def test_change_rate(mixed_result):
    # 3 differing out of 5 total
    s = summarize(mixed_result)
    assert abs(s.change_rate - 3 / 5) < 1e-9


def test_change_rate_empty(empty_result):
    assert summarize(empty_result).change_rate == 0.0


def test_returns_env_summary_instance(mixed_result):
    assert isinstance(summarize(mixed_result), EnvSummary)


# ---------------------------------------------------------------------------
# format_summary_text()
# ---------------------------------------------------------------------------


def test_format_contains_total(mixed_result):
    text = format_summary_text(summarize(mixed_result))
    assert "5" in text


def test_format_contains_change_rate(mixed_result):
    text = format_summary_text(summarize(mixed_result))
    assert "%" in text


def test_format_with_label(mixed_result):
    text = format_summary_text(summarize(mixed_result), label="prod-vs-staging")
    assert "prod-vs-staging" in text


def test_format_without_label_no_bracket(mixed_result):
    text = format_summary_text(summarize(mixed_result))
    assert "[" not in text
