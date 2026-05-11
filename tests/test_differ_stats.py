"""Tests for envdiff.differ_stats."""
import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.differ_stats import ChangeStats, compute_stats, format_stats_text


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _entry(key: str, status: DiffStatus) -> DiffEntry:
    staging = "s" if status != DiffStatus.ADDED else None
    production = "p" if status != DiffStatus.REMOVED else None
    return DiffEntry(key=key, status=status, staging_value=staging, production_value=production)


@pytest.fixture()
def mixed_result() -> DiffResult:
    entries = [
        _entry("A", DiffStatus.ADDED),
        _entry("B", DiffStatus.ADDED),
        _entry("C", DiffStatus.REMOVED),
        _entry("D", DiffStatus.CHANGED),
        _entry("E", DiffStatus.CHANGED),
        _entry("F", DiffStatus.UNCHANGED),
    ]
    return DiffResult(entries=entries)


@pytest.fixture()
def empty_result() -> DiffResult:
    return DiffResult(entries=[])


# ---------------------------------------------------------------------------
# compute_stats
# ---------------------------------------------------------------------------

def test_total_count(mixed_result):
    stats = compute_stats(mixed_result)
    assert stats.total == 6


def test_added_count(mixed_result):
    assert compute_stats(mixed_result).added == 2


def test_removed_count(mixed_result):
    assert compute_stats(mixed_result).removed == 1


def test_changed_count(mixed_result):
    assert compute_stats(mixed_result).changed == 2


def test_unchanged_count(mixed_result):
    assert compute_stats(mixed_result).unchanged == 1


def test_change_ratio(mixed_result):
    stats = compute_stats(mixed_result)
    # (2 added + 1 removed + 2 changed) / 6
    assert abs(stats.change_ratio - 5 / 6) < 1e-9


def test_churn_score(mixed_result):
    stats = compute_stats(mixed_result)
    # 1*1.5 + 2*1.0 + 2*0.5 = 1.5 + 2.0 + 1.0 = 4.5
    assert abs(stats.churn_score - 4.5) < 1e-9


def test_empty_result_zero_ratio(empty_result):
    stats = compute_stats(empty_result)
    assert stats.change_ratio == 0.0
    assert stats.churn_score == 0.0
    assert stats.total == 0


def test_returns_change_stats_instance(mixed_result):
    assert isinstance(compute_stats(mixed_result), ChangeStats)


# ---------------------------------------------------------------------------
# format_stats_text
# ---------------------------------------------------------------------------

def test_format_contains_total(mixed_result):
    text = format_stats_text(compute_stats(mixed_result))
    assert "6" in text


def test_format_contains_label():
    result = DiffResult(entries=[])
    text = format_stats_text(compute_stats(result), label="prod")
    assert "prod" in text


def test_format_no_label_default():
    result = DiffResult(entries=[])
    text = format_stats_text(compute_stats(result))
    assert "Change Stats" in text
    assert "—" not in text


def test_format_contains_churn_score(mixed_result):
    text = format_stats_text(compute_stats(mixed_result))
    assert "Churn score" in text
