"""Tests for envdiff.deduplicator."""
import pytest

from envdiff.deduplicator import (
    DeduplicationReport,
    DuplicateEntry,
    find_duplicates,
    resolve_duplicates,
)


@pytest.fixture()
def staging() -> dict:
    return {"HOST": "staging.example.com", "PORT": "8080", "ONLY_STAGING": "yes"}


@pytest.fixture()
def production() -> dict:
    return {"HOST": "prod.example.com", "PORT": "8080", "ONLY_PROD": "true"}


# --- find_duplicates ---

def test_find_duplicates_returns_report(staging, production):
    report = find_duplicates(staging, production)
    assert isinstance(report, DeduplicationReport)


def test_find_duplicates_total_count(staging, production):
    report = find_duplicates(staging, production)
    assert report.total == 2  # HOST and PORT


def test_find_duplicates_matching_values(staging, production):
    report = find_duplicates(staging, production)
    matching_keys = [d.key for d in report.matching]
    assert "PORT" in matching_keys


def test_find_duplicates_conflicting_values(staging, production):
    report = find_duplicates(staging, production)
    conflicting_keys = [d.key for d in report.conflicting]
    assert "HOST" in conflicting_keys


def test_find_duplicates_no_shared_keys():
    report = find_duplicates({"A": "1"}, {"B": "2"})
    assert report.total == 0
    assert report.matching == []
    assert report.conflicting == []


def test_duplicate_entry_values_match():
    entry = DuplicateEntry(key="PORT", staging_value="8080", production_value="8080")
    assert entry.values_match is True


def test_duplicate_entry_values_differ():
    entry = DuplicateEntry(key="HOST", staging_value="staging.host", production_value="prod.host")
    assert entry.values_match is False


# --- resolve_duplicates ---

def test_resolve_prefers_production_by_default(staging, production):
    merged, _ = resolve_duplicates(staging, production)
    assert merged["HOST"] == "prod.example.com"


def test_resolve_prefers_staging(staging, production):
    merged, _ = resolve_duplicates(staging, production, prefer="staging")
    assert merged["HOST"] == "staging.example.com"


def test_resolve_includes_unique_staging_keys(staging, production):
    merged, _ = resolve_duplicates(staging, production)
    assert "ONLY_STAGING" in merged


def test_resolve_includes_unique_production_keys(staging, production):
    merged, _ = resolve_duplicates(staging, production)
    assert "ONLY_PROD" in merged


def test_resolve_returns_report(staging, production):
    _, report = resolve_duplicates(staging, production)
    assert isinstance(report, DeduplicationReport)
    assert report.total == 2


def test_resolve_invalid_prefer_raises(staging, production):
    with pytest.raises(ValueError, match="prefer must be"):
        resolve_duplicates(staging, production, prefer="both")
