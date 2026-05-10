"""Tests for envdiff.reporter."""

from __future__ import annotations

import json

import pytest

from envdiff.differ import diff
from envdiff.reporter import build_report, report_json


@pytest.fixture()
def staging() -> dict[str, str]:
    return {
        "APP_ENV": "staging",
        "DB_HOST": "localhost",
        "SECRET_KEY": "abc123",
        "LOG_LEVEL": "DEBUG",
    }


@pytest.fixture()
def production() -> dict[str, str]:
    return {
        "APP_ENV": "production",
        "DB_HOST": "db.prod.example.com",
        "SECRET_KEY": "abc123",
        "NEW_RELIC_KEY": "nr-xyz",
    }


def test_summary_counts(staging, production):
    result = diff(staging, production)
    report = build_report(result)
    summary = report["summary"]
    assert summary["added"] == 1    # NEW_RELIC_KEY
    assert summary["removed"] == 1  # LOG_LEVEL
    assert summary["changed"] == 2  # APP_ENV, DB_HOST
    assert summary["unchanged"] == 1  # SECRET_KEY


def test_differences_excludes_unchanged(staging, production):
    result = diff(staging, production)
    report = build_report(result)
    keys = [e["key"] for e in report["differences"]]
    assert "SECRET_KEY" not in keys
    assert "APP_ENV" in keys


def test_added_entry_shape(staging, production):
    result = diff(staging, production)
    report = build_report(result)
    added = [e for e in report["differences"] if e["status"] == "added"]
    assert len(added) == 1
    entry = added[0]
    assert entry["key"] == "NEW_RELIC_KEY"
    assert entry["production_value"] == "nr-xyz"
    assert "staging_value" not in entry


def test_removed_entry_shape(staging, production):
    result = diff(staging, production)
    report = build_report(result)
    removed = [e for e in report["differences"] if e["status"] == "removed"]
    assert len(removed) == 1
    entry = removed[0]
    assert entry["key"] == "LOG_LEVEL"
    assert entry["staging_value"] == "DEBUG"
    assert "production_value" not in entry


def test_changed_entry_has_both_values(staging, production):
    result = diff(staging, production)
    report = build_report(result)
    changed = [e for e in report["differences"] if e["status"] == "changed"]
    for entry in changed:
        assert "staging_value" in entry
        assert "production_value" in entry


def test_report_json_is_valid_json(staging, production):
    result = diff(staging, production)
    raw = report_json(result)
    parsed = json.loads(raw)
    assert "summary" in parsed
    assert "differences" in parsed


def test_identical_envs_produce_empty_differences():

    env = {"FOO": "bar", "BAZ": "qux"}
    result = diff(env, env)
    report = build_report(result)
    assert report["differences"] == []
    assert report["summary"]["added"] == 0
    assert report["summary"]["removed"] == 0
    assert report["summary"]["changed"] == 0


def test_summary_counts_sum_to_total_keys(staging, production):
    """Verify that all summary counts add up to the total number of unique keys."""
    result = diff(staging, production)
    report = build_report(result)
    summary = report["summary"]
    total_unique_keys = len(set(staging) | set(production))
    assert summary["added"] + summary["removed"] + summary["changed"] + summary["unchanged"] == total_unique_keys
