"""Tests for envdiff.profiler."""
import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.profiler import EnvProfile, profile_diff


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mixed_result() -> DiffResult:
    entries = [
        DiffEntry(key="DB_HOST", staging="localhost", production="prod-db", status=DiffStatus.CHANGED),
        DiffEntry(key="DB_PASSWORD", staging="secret", production="secret", status=DiffStatus.UNCHANGED),
        DiffEntry(key="NEW_FEATURE", staging=None, production="1", status=DiffStatus.ADDED),
        DiffEntry(key="OLD_KEY", staging="old", production=None, status=DiffStatus.REMOVED),
        DiffEntry(key="APP_ENV", staging="staging", production="production", status=DiffStatus.CHANGED),
        DiffEntry(key="LOG_LEVEL", staging="debug", production="debug", status=DiffStatus.UNCHANGED),
        DiffEntry(key="API_TOKEN", staging="tok-stg", production="tok-prd", status=DiffStatus.CHANGED),
    ]
    return DiffResult(entries=entries)


@pytest.fixture()
def empty_result() -> DiffResult:
    return DiffResult(entries=[])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_total_count(mixed_result):
    prof = profile_diff(mixed_result)
    assert prof.total == 7


def test_added_count(mixed_result):
    prof = profile_diff(mixed_result)
    assert prof.added == 1


def test_removed_count(mixed_result):
    prof = profile_diff(mixed_result)
    assert prof.removed == 1


def test_changed_count(mixed_result):
    prof = profile_diff(mixed_result)
    assert prof.changed == 3


def test_unchanged_count(mixed_result):
    prof = profile_diff(mixed_result)
    assert prof.unchanged == 2


def test_change_rate(mixed_result):
    prof = profile_diff(mixed_result)
    # (1 added + 1 removed + 3 changed) / 7 total
    assert abs(prof.change_rate - 5 / 7) < 1e-9


def test_sensitive_keys_detected(mixed_result):
    prof = profile_diff(mixed_result)
    assert "DB_PASSWORD" in prof.sensitive_keys
    assert "API_TOKEN" in prof.sensitive_keys


def test_non_sensitive_key_excluded(mixed_result):
    prof = profile_diff(mixed_result)
    assert "LOG_LEVEL" not in prof.sensitive_keys
    assert "APP_ENV" not in prof.sensitive_keys


def test_prefix_grouping(mixed_result):
    prof = profile_diff(mixed_result)
    assert prof.prefixes.get("DB") == 2  # DB_HOST, DB_PASSWORD
    assert prof.prefixes.get("APP") == 1
    assert prof.prefixes.get("LOG") == 1


def test_empty_result_zero_counts(empty_result):
    prof = profile_diff(empty_result)
    assert prof.total == 0
    assert prof.added == 0
    assert prof.change_rate == 0.0


def test_empty_result_no_sensitive_keys(empty_result):
    prof = profile_diff(empty_result)
    assert prof.sensitive_keys == []


def test_all_unchanged_change_rate_zero():
    entries = [
        DiffEntry(key="FOO", staging="bar", production="bar", status=DiffStatus.UNCHANGED),
    ]
    result = DiffResult(entries=entries)
    prof = profile_diff(result)
    assert prof.change_rate == 0.0


def test_returns_env_profile_instance(mixed_result):
    prof = profile_diff(mixed_result)
    assert isinstance(prof, EnvProfile)
