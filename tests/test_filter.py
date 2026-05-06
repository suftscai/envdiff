"""Tests for envdiff.filter."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.filter import (
    exclude_unchanged,
    filter_by_pattern,
    filter_by_prefix,
    filter_by_regex,
    filter_by_status,
)


def _entry(key: str, status: DiffStatus) -> DiffEntry:
    return DiffEntry(key=key, status=status, staging_value="a", production_value="b")


@pytest.fixture()
def mixed_result() -> DiffResult:
    return DiffResult(
        entries=[
            _entry("APP_HOST", DiffStatus.UNCHANGED),
            _entry("APP_PORT", DiffStatus.CHANGED),
            _entry("DB_URL", DiffStatus.ADDED),
            _entry("DB_PASS", DiffStatus.REMOVED),
            _entry("CACHE_TTL", DiffStatus.UNCHANGED),
            _entry("AWS_KEY", DiffStatus.ADDED),
        ]
    )


def test_filter_by_status_single(mixed_result):
    result = filter_by_status(mixed_result, [DiffStatus.ADDED])
    assert all(e.status == DiffStatus.ADDED for e in result.entries)
    assert len(result.entries) == 2


def test_filter_by_status_multiple(mixed_result):
    result = filter_by_status(mixed_result, [DiffStatus.ADDED, DiffStatus.REMOVED])
    assert len(result.entries) == 3


def test_filter_by_status_empty_set(mixed_result):
    result = filter_by_status(mixed_result, [])
    assert result.entries == []


def test_filter_by_prefix(mixed_result):
    result = filter_by_prefix(mixed_result, "DB_")
    assert {e.key for e in result.entries} == {"DB_URL", "DB_PASS"}


def test_filter_by_prefix_no_match(mixed_result):
    result = filter_by_prefix(mixed_result, "NONEXISTENT_")
    assert result.entries == []


def test_filter_by_pattern_wildcard(mixed_result):
    result = filter_by_pattern(mixed_result, "APP_*")
    assert {e.key for e in result.entries} == {"APP_HOST", "APP_PORT"}


def test_filter_by_pattern_question_mark(mixed_result):
    result = filter_by_pattern(mixed_result, "DB_???")
    assert {e.key for e in result.entries} == {"DB_URL"}


def test_filter_by_regex(mixed_result):
    result = filter_by_regex(mixed_result, r"^(APP|AWS)_")
    assert {e.key for e in result.entries} == {"APP_HOST", "APP_PORT", "AWS_KEY"}


def test_filter_by_regex_invalid_raises(mixed_result):
    import re
    with pytest.raises(re.error):
        filter_by_regex(mixed_result, r"[invalid")


def test_exclude_unchanged(mixed_result):
    result = exclude_unchanged(mixed_result)
    assert all(e.status != DiffStatus.UNCHANGED for e in result.entries)
    assert len(result.entries) == 4


def test_original_result_not_mutated(mixed_result):
    original_len = len(mixed_result.entries)
    exclude_unchanged(mixed_result)
    assert len(mixed_result.entries) == original_len
